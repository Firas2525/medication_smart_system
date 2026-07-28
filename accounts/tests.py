from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class PatientListAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin_user',
            password='123456',
            user_type='supervisor',
            is_staff=True,
            is_superuser=True,
            is_approved=True,
        )
        self.patient_one = User.objects.create_user(
            username='patient_one',
            password='123456',
            user_type='patient',
            is_approved=True,
        )
        self.patient_two = User.objects.create_user(
            username='patient_two',
            password='123456',
            user_type='patient',
            is_approved=True,
        )
        self.doctor = User.objects.create_user(
            username='doctor_one',
            password='123456',
            user_type='doctor',
            is_approved=True,
        )

    def test_admin_can_list_all_patients(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get('/accounts/api/patients/all/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        usernames = [item['username'] for item in response.data['data']]
        self.assertIn('patient_one', usernames)
        self.assertIn('patient_two', usernames)
        self.assertNotIn('doctor_one', usernames)

    def test_doctor_registration_accepts_plain_filename(self):
        response = self.client.post('/accounts/api/register/doctor/', {
            'username': 'doctor_plain',
            'email': 'doctor_plain@example.com',
            'password': '123456',
            'first_name': 'أحمد',
            'last_name': 'محمد',
            'phone_number': '0500000000',
            'specialization': 'قلب',
            'license_number': '12345',
            'license_image_url': 'certificate.jpg',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')

