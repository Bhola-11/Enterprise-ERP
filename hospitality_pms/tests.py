from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from organizations.models import Organization, Branch
from accounting.models import Account
from hospitality_pms.models import (
    RoomType, HotelRoom, GuestProfile, RoomReservation,
    GuestFolioInvoice, FolioChargeLine
)
from hospitality_pms.services import FrontDeskService, FolioBillingService

User = get_user_model()

class HospitalityPMSTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='front_desk_mgr', email='hotel@nexora.io', password='Password123!', role='MANAGER')
        self.org = Organization.objects.create(name='Nexora Grand Resort')
        self.branch = Branch.objects.create(organization=self.org, name='Miami Beach Resort', code='HTL-01')
        self.cash_acc = Account.objects.create(
            code='1010', name='Front Desk Cash', account_type='ASSET', is_active=True
        )
        self.ar_acc = Account.objects.create(
            code='1140', name='Guest Ledger AR', account_type='ASSET', is_active=True
        )

        self.room_type = RoomType.objects.create(
            code='OCEAN-KING', name='Oceanfront King Suite', base_occupancy=2, max_occupancy=3,
            base_nightly_rate=Decimal('350.00')
        )
        self.room = HotelRoom.objects.create(
            room_number='501', room_type=self.room_type, floor=5, status='AVAILABLE'
        )
        self.guest = GuestProfile.objects.create(
            first_name='Sophia', last_name='Vanderbilt', email='sophia@vanderbilt.com',
            phone='+1-305-555-4433', vip_tier='PLATINUM'
        )

        self.client = Client()
        self.client.force_login(self.user)

    def test_reservation_lifecycle_and_folio_settlement(self):
        reservation = RoomReservation.objects.create(
            confirmation_code='RES-HTL-9988', guest=self.guest, room_type=self.room_type,
            room=self.room, check_in_date='2026-09-15', check_out_date='2026-09-17',
            number_of_guests=2, nightly_rate=Decimal('350.00'), total_room_charge=Decimal('700.00'),
            deposit_paid=Decimal('100.00'), status='CONFIRMED'
        )

        # Check in
        folio = FrontDeskService.process_check_in(reservation)
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'OCCUPIED')
        self.assertEqual(folio.status, 'OPEN')

        # Add incidental
        FolioBillingService.post_charge(folio, 'RESTAURANT', 'Room Service Lobster Dinner', Decimal('120.00'))
        folio.refresh_from_db()
        self.assertEqual(folio.total_incidentals, Decimal('120.00'))

        # Check out
        FrontDeskService.process_check_out(reservation, user=self.user)
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, 'CLEANING')
        folio.refresh_from_db()
        self.assertEqual(folio.status, 'SETTLED')
        self.assertIsNotNone(folio.journal_entry)

    def test_views(self):
        res_dash = self.client.get(reverse('hospitality_pms:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_rack = self.client.get(reverse('hospitality_pms:room_matrix'))
        self.assertEqual(res_rack.status_code, 200)
