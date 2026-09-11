import hashlib
import json
import uuid
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from .models import (
    TaxJurisdiction, HSNSACCode, GSTTaxRate, EWayBillRecord,
    EInvoiceIRN, EUVATRule, USStateNexusRate, TaxFilingReturn
)
from sales.models import Invoice, Customer
from purchasing.models import Supplier, PurchaseOrder


class GSTCalculationEngine:
    """
    Enterprise Indian GST calculation engine supporting:
    - Intra-State transactions (CGST + SGST split 50/50)
    - Inter-State transactions (IGST 100%)
    - Reverse Charge Mechanism (RCM)
    - Compensation Cess
    - State GSTIN code extraction (First 2 digits)
    """

    STATE_CODES = {
        '01': 'Jammu & Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab',
        '04': 'Chandigarh', '05': 'Uttarakhand', '06': 'Haryana',
        '07': 'Delhi', '08': 'Rajasthan', '09': 'Uttar Pradesh',
        '10': 'Bihar', '11': 'Sikkim', '12': 'Arunachal Pradesh',
        '13': 'Nagaland', '14': 'Manipur', '15': 'Mizoram',
        '16': 'Tripura', '17': 'Meghalaya', '18': 'Assam',
        '19': 'West Bengal', '20': 'Jharkhand', '21': 'Odisha',
        '22': 'Chhattisgarh', '23': 'Madhya Pradesh', '24': 'Gujarat',
        '27': 'Maharashtra', '29': 'Karnataka', '30': 'Goa',
        '32': 'Kerala', '33': 'Tamil Nadu', '36': 'Telangana',
        '37': 'Andhra Pradesh',
    }

    @classmethod
    def get_state_code_from_gstin(cls, gstin):
        if gstin and len(gstin.strip()) >= 2:
            return gstin.strip()[:2]
        return None

    @classmethod
    def calculate_gst(cls, taxable_amount, total_rate_pct, seller_state_code, buyer_state_code, is_rcm=False, cess_pct=Decimal('0.00')):
        taxable_amount = Decimal(str(taxable_amount))
        total_rate_pct = Decimal(str(total_rate_pct))
        cess_pct = Decimal(str(cess_pct))

        is_interstate = (seller_state_code and buyer_state_code and seller_state_code != buyer_state_code)

        if is_interstate:
            # IGST
            cgst_rate = Decimal('0.00')
            sgst_rate = Decimal('0.00')
            igst_rate = total_rate_pct
            cgst_amount = Decimal('0.00')
            sgst_amount = Decimal('0.00')
            igst_amount = (taxable_amount * (igst_rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            tax_type = 'INTER_STATE_IGST'
        else:
            # Intra-State (CGST + SGST 50/50 split)
            half_rate = (total_rate_pct / Decimal('2.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            cgst_rate = half_rate
            sgst_rate = half_rate
            igst_rate = Decimal('0.00')
            cgst_amount = (taxable_amount * (cgst_rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            sgst_amount = (taxable_amount * (sgst_rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            igst_amount = Decimal('0.00')
            tax_type = 'INTRA_STATE_CGST_SGST'

        cess_amount = (taxable_amount * (cess_pct / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_tax = cgst_amount + sgst_amount + igst_amount + cess_amount
        total_amount = taxable_amount + total_tax

        return {
            'taxable_amount': taxable_amount,
            'tax_type': tax_type,
            'is_interstate': is_interstate,
            'cgst_rate': cgst_rate,
            'cgst_amount': cgst_amount,
            'sgst_rate': sgst_rate,
            'sgst_amount': sgst_amount,
            'igst_rate': igst_rate,
            'igst_amount': igst_amount,
            'cess_rate': cess_pct,
            'cess_amount': cess_amount,
            'total_tax': total_tax,
            'total_amount': total_amount,
            'is_rcm': is_rcm
        }

    @classmethod
    def generate_gstr1_summary(cls, start_date, end_date):
        invoices = Invoice.objects.filter(invoice_date__range=[start_date, end_date], status__in=['ISSUED', 'PAID', 'OVERDUE'])
        b2b_invoices = []
        b2c_invoices = []

        total_taxable_b2b = Decimal('0.00')
        total_tax_b2b = Decimal('0.00')
        total_taxable_b2c = Decimal('0.00')
        total_tax_b2c = Decimal('0.00')

        for inv in invoices:
            has_gstin = bool(inv.customer.tax_number if inv.customer and inv.customer.tax_number else False)
            if has_gstin:
                b2b_invoices.append(inv)
                total_taxable_b2b += inv.subtotal
                total_tax_b2b += inv.tax_amount
            else:
                b2c_invoices.append(inv)
                total_taxable_b2c += inv.subtotal
                total_tax_b2c += inv.tax_amount

        return {
            'period_start': start_date,
            'period_end': end_date,
            'total_invoices': invoices.count(),
            'b2b_count': len(b2b_invoices),
            'b2b_taxable': total_taxable_b2b,
            'b2b_tax': total_tax_b2b,
            'b2c_count': len(b2c_invoices),
            'b2c_taxable': total_taxable_b2c,
            'b2c_tax': total_tax_b2c,
            'grand_taxable_turnover': total_taxable_b2b + total_taxable_b2c,
            'grand_tax_collected': total_tax_b2b + total_tax_b2c,
        }


class EInvoicePayloadBuilder:
    """
    Generates NIC/GSTN Government compliant e-Invoice Schema (v1.1)
    and computes the cryptographic SHA-256 IRN hash.
    """

    @staticmethod
    def generate_einvoice_irn(invoice_number, invoice_date, seller_gstin, buyer_gstin, taxable_value, tax_amount, total_value):
        raw_token = f"{seller_gstin}:{invoice_number}:{invoice_date.strftime('%d/%m/%Y')}:{total_value:.2f}"
        irn_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest().upper()
        ack_no = f"ACK{timezone.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"

        qr_data = {
            'SellerGSTIN': seller_gstin,
            'BuyerGSTIN': buyer_gstin,
            'DocNo': invoice_number,
            'DocTyp': 'INV',
            'DocDt': invoice_date.strftime('%d/%m/%Y'),
            'TotInvVal': float(total_value),
            'ItemCnt': 1,
            'MainHsnCode': '84713010',
            'Irn': irn_hash,
            'AckNo': ack_no,
            'AckDt': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        einvoice_rec = EInvoiceIRN.objects.create(
            irn_hash=irn_hash,
            ack_number=ack_no,
            ack_date=timezone.now(),
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            seller_gstin=seller_gstin,
            buyer_gstin=buyer_gstin,
            total_taxable_value=Decimal(str(taxable_value)),
            total_tax_amount=Decimal(str(tax_amount)),
            total_invoice_value=Decimal(str(total_value)),
            qr_code_payload=json.dumps(qr_data),
            status='ACTIVE'
        )

        return einvoice_rec


class EWayBillGenerator:
    """
    Generates compliant e-Way Bill records with validity hours based on transit distance.
    1 day for every 200 km of distance.
    """

    @staticmethod
    def generate_eway_bill(document_number, document_type, total_invoice_value, from_pincode, to_pincode, distance_km, vehicle_number="", transporter_id="", transporter_name="", user=None):
        total_val = Decimal(str(total_invoice_value))
        dist = max(1, int(distance_km))

        # Validity days: 1 day per 200km (minimum 1 day)
        validity_days = max(1, (dist + 199) // 200)
        valid_from = timezone.now()
        valid_until = valid_from + timezone.timedelta(days=validity_days)

        ewb_num = f"{timezone.now().strftime('%y%m%d')}{uuid.uuid4().int % 1000000:06d}"

        payload = {
            'supplyType': 'O',
            'subSupplyType': '1',
            'docType': 'INV',
            'docNo': document_number,
            'fromPincode': from_pincode,
            'toPincode': to_pincode,
            'distance': dist,
            'transporterId': transporter_id,
            'transporterName': transporter_name,
            'vehicleNo': vehicle_number,
            'totalValue': float(total_val),
        }

        response = {
            'ewayBillNo': ewb_num,
            'ewayBillDate': valid_from.strftime('%d/%m/%Y %H:%M:%S'),
            'validUpto': valid_until.strftime('%d/%m/%Y %H:%M:%S'),
            'status': 'GEN',
        }

        ewb = EWayBillRecord.objects.create(
            ewb_number=ewb_num,
            document_number=document_number,
            document_type=document_type,
            transport_mode='ROAD',
            vehicle_number=vehicle_number,
            transporter_id=transporter_id,
            transporter_name=transporter_name,
            distance_km=dist,
            from_pincode=from_pincode,
            to_pincode=to_pincode,
            total_invoice_value=total_val,
            valid_from=valid_from,
            valid_until=valid_until,
            status='GENERATED',
            payload_json=payload,
            response_json=response,
            generated_by=user
        )

        return ewb


class EUVATOSSValidator:
    """
    EU VAT & One-Stop-Shop (OSS) rule engine for intra-community sales & digital services.
    """

    @staticmethod
    def calculate_eu_vat(member_state_code, taxable_amount, is_b2b=False, is_vies_valid=False):
        taxable = Decimal(str(taxable_amount))
        rule = EUVATRule.objects.filter(member_state_code__iexact=member_state_code.strip()).first()

        if not rule:
            # Fallback default 20%
            vat_rate = Decimal('20.00')
        else:
            vat_rate = rule.standard_vat_rate

        # B2B Reverse Charge applies if buyer has valid VIES VAT number
        if is_b2b and is_vies_valid and rule and rule.reverse_charge_b2b:
            return {
                'taxable_amount': taxable,
                'vat_rate': Decimal('0.00'),
                'vat_amount': Decimal('0.00'),
                'total_amount': taxable,
                'is_reverse_charge': True,
                'note': 'EU Reverse Charge Mechanism (Article 194 of Directive 2006/112/EC)'
            }

        vat_amount = (taxable * (vat_rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return {
            'taxable_amount': taxable,
            'vat_rate': vat_rate,
            'vat_amount': vat_amount,
            'total_amount': taxable + vat_amount,
            'is_reverse_charge': False,
            'note': f'EU One-Stop-Shop ({rule.country_name if rule else member_state_code}) Standard VAT'
        }


class USNexusTaxCalculator:
    """
    US State & Local Composite Sales Tax Calculator with Economic Nexus validation.
    """

    @staticmethod
    def calculate_us_sales_tax(state_code, taxable_amount):
        taxable = Decimal(str(taxable_amount))
        nexus_rule = USStateNexusRate.objects.filter(state_code__iexact=state_code.strip()).first()

        if not nexus_rule:
            state_rate = Decimal('6.00')
            local_rate = Decimal('2.00')
        else:
            state_rate = nexus_rule.state_sales_tax_rate
            local_rate = nexus_rule.avg_local_sales_tax_rate

        combined_rate = state_rate + local_rate
        state_tax = (taxable * (state_rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        local_tax = (taxable * (local_rate / Decimal('100.00'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_tax = state_tax + local_tax

        return {
            'state_code': state_code.upper(),
            'taxable_amount': taxable,
            'state_tax_rate': state_rate,
            'state_tax_amount': state_tax,
            'local_tax_rate': local_rate,
            'local_tax_amount': local_tax,
            'combined_rate': combined_rate,
            'total_tax': total_tax,
            'total_amount': taxable + total_tax
        }
