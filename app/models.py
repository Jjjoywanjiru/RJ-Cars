# app/models.py
import uuid
from datetime import datetime

class MpesaPayment:
    """Model for M-Pesa payment transactions"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.table = 'mpesa_payments'
    
    def create(self, listing_id, phone_number, amount, checkout_request_id, account_reference, transaction_desc):
        """Create a new M-Pesa payment record"""
        payment_data = {
            "id": str(uuid.uuid4()),
            "listing_id": listing_id,
            "phone_number": phone_number,
            "amount": amount,
            "checkout_request_id": checkout_request_id,
            "account_reference": account_reference,
            "transaction_desc": transaction_desc,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        result = self.supabase.table(self.table).insert(payment_data).execute()
        return result.data[0] if result.data else None
    
    def update_status(self, checkout_request_id, status, mpesa_receipt_number=None, transaction_date=None):
        """Update the status of a payment"""
        update_data = {
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        if mpesa_receipt_number:
            update_data["mpesa_receipt_number"] = mpesa_receipt_number
            
        if transaction_date:
            update_data["transaction_date"] = transaction_date
        
        result = self.supabase.table(self.table)\
            .update(update_data)\
            .eq("checkout_request_id", checkout_request_id)\
            .execute()
            
        return result.data[0] if result.data else None
    
    def get_by_checkout_request_id(self, checkout_request_id):
        """Get payment by checkout request ID"""
        result = self.supabase.table(self.table)\
            .select("*")\
            .eq("checkout_request_id", checkout_request_id)\
            .execute()
            
        return result.data[0] if result.data else None
    
    def get_by_listing_id(self, listing_id):
        """Get payments by listing ID"""
        result = self.supabase.table(self.table)\
            .select("*")\
            .eq("listing_id", listing_id)\
            .execute()
            
        return result.data if result.data else []