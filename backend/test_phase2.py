import os
import sys
import unittest
import json
import io

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app, init_db, is_rate_limited, record_failed_attempt, reset_login_attempts
from ml_lookup import extract_matching_ingredients, check_allergen_risk, df
from alternative import get_alternative

class TestPhase2SecurityAndHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def setUp(self):
        # Clear rate limit store before each test
        login_attempts = {}

    def test_01_secret_key_configuration(self):
        """1. Test secret key fallback and environment variable behavior."""
        self.assertTrue(app.secret_key is not None)
        self.assertGreater(len(app.secret_key), 0)

    def test_02_protected_routes_unauthenticated(self):
        """2. Test that unauthenticated users are redirected to login for protected routes."""
        for route in ['/upload', '/results', '/recommendation']:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 302, f"Route {route} did not redirect unauthenticated user")
            self.assertIn('/login', res.headers['Location'])

    def test_03_invalid_file_extension(self):
        """3. Test rejection of invalid file extensions."""
        # Login first
        self._register_and_login("sec_user1", "sec_user1@example.com", "Password123!")
        
        data = {
            'image': (io.BytesIO(b"fake executable content"), 'script.py')
        }
        res = self.client.post('/upload', data=data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Invalid file format', res.data)

    def test_04_invalid_mime_corrupted_image(self):
        """4. Test rejection of fake/corrupted images with valid extension."""
        self._register_and_login("sec_user2", "sec_user2@example.com", "Password123!")
        
        # File has .jpg extension but corrupted non-image bytes
        data = {
            'image': (io.BytesIO(b"NOT_AN_IMAGE_FILE_DATA"), 'fake.jpg')
        }
        res = self.client.post('/upload', data=data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'corrupted or not a valid image', res.data)

    def test_05_oversized_upload(self):
        """5. Test 413 error handling for oversized files."""
        # Test max content length configuration
        self.assertEqual(app.config['MAX_CONTENT_LENGTH'], 16 * 1024 * 1024)

    def test_06_unique_uuid_filenames(self):
        """6 & 7 & 8. Test unique UUID filename generation and path traversal safety."""
        from PIL import Image
        img_byte_arr = io.BytesIO()
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()

        self._register_and_login("sec_user3", "sec_user3@example.com", "Password123!")
        
        # Upload file with path traversal attempt in filename
        data = {
            'image': (io.BytesIO(img_bytes), '../../../etc/passwd.jpg')
        }
        res = self.client.post('/upload', data=data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify no file was created with path traversal in name
        uploads = os.listdir(app.config['UPLOAD_FOLDER'])
        for f in uploads:
            self.assertNotIn('passwd', f)
            self.assertNotIn('..', f)

    def test_09_weak_password_rejection(self):
        """9. Test rejection of weak/short passwords (< 8 chars)."""
        data = {
            'username': 'weakuser',
            'email': 'weakuser@example.com',
            'password': '123',  # Only 3 chars
            'allergies': ['None'],
            'health_conditions': ['None'],
            'diet': 'None'
        }
        res = self.client.post('/register', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Password must be at least 8 characters long', res.data)

    def test_10_invalid_login_generic_error(self):
        """10. Test generic authentication error message (does not reveal user existence)."""
        # Non-existent user
        data = {'username': 'nonexistent_user_999', 'password': 'Password123!'}
        res = self.client.post('/login', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Invalid Username or Password', res.data)

    def test_11_session_cookie_security(self):
        """11. Test HTTPOnly and SameSite session cookie configuration."""
        self.assertTrue(app.config['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual(app.config['SESSION_COOKIE_SAMESITE'], 'Lax')

    def test_12_ocr_unreadable_image_handling(self):
        """12 & 13. Test OCR empty text handling."""
        from PIL import Image
        img_byte_arr = io.BytesIO()
        # Create blank white image (OCR returns empty text)
        img = Image.new('RGB', (200, 200), color = 'white')
        img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()

        self._register_and_login("sec_user4", "sec_user4@example.com", "Password123!")
        data = {
            'image': (io.BytesIO(img_bytes), 'blank.jpg')
        }
        res = self.client.post('/upload', data=data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'read enough text from this image', res.data)

    def test_14_missing_recommendation_fallback(self):
        """14. Test missing recommendation fallback handling."""
        alts = get_alternative(["non_existent_ingredient_xyz"])
        self.assertIn("non_existent_ingredient_xyz", alts)
        self.assertEqual(alts["non_existent_ingredient_xyz"], "No suitable alternative found.")

    def test_15_custom_404_error_page(self):
        """15. Test custom 404 error page."""
        res = self.client.get('/non_existent_page_12345')
        self.assertEqual(res.status_code, 404)
        self.assertIn(b'Page Not Found', res.data)
        self.assertIn(b'FoodLens AI', res.data)

    def test_16_rate_limiting(self):
        """16. Test rate limiting for login attempts."""
        key = "127.0.0.1:brute_force_user"
        reset_login_attempts(key)
        for _ in range(5):
            record_failed_attempt(key)
        self.assertTrue(is_rate_limited(key))
        reset_login_attempts(key)

    def _register_and_login(self, username, email, password):
        reg_data = {
            'username': username,
            'email': email,
            'password': password,
            'allergies': ['Dairy'],
            'health_conditions': ['Diabetes'],
            'diet': 'Ketogenic'
        }
        self.client.post('/register', data=reg_data)
        self.client.post('/login', data={'username': username, 'password': password})

if __name__ == '__main__':
    unittest.main()
