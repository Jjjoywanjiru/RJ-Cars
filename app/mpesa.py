# app/mpesa.py
import os
import base64
import requests
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MpesaClient:
    """M-Pesa API client to handle STK Push payments"""
    
    def __init__(self, app=None):
        self.app = app
        self.api_url = "https://sandbox.safaricom.co.ke"  # Change to production URL for live environment
        self.access_token = None
        self.business_shortcode = None
        self.passkey = None
        self.callback_url = None
        self.consumer_key = None
        self.consumer_secret = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the M-Pesa client with Flask app configuration"""
        self.app = app
        self.business_shortcode = app.config.get('MPESA_BUSINESS_SHORTCODE')
        self.passkey = app.config.get('MPESA_PASSKEY')
        self.callback_url = app.config.get('MPESA_CALLBACK_URL')
        self.consumer_key = app.config.get('MPESA_CONSUMER_KEY')
        self.consumer_secret = app.config.get('MPESA_CONSUMER_SECRET')
    
    def get_access_token(self):
        """Get OAuth access token from M-Pesa API"""
        try:
            url = f"{self.api_url}/oauth/v1/generate?grant_type=client_credentials"
            
            # Encode consumer key and secret for basic auth
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode('utf-8')
            
            headers = {
                "Authorization": f"Basic {encoded_auth}"
            }
            
            response = requests.get(url, headers=headers)
            response_data = response.json()
            
            if 'access_token' in response_data:
                self.access_token = response_data['access_token']
                return self.access_token
            else:
                logger.error(f"Failed to get access token: {response_data}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None
    
    def generate_password(self):
        """Generate the M-Pesa API password using the provided passkey"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.business_shortcode}{self.passkey}{timestamp}"
        encoded_password = base64.b64encode(password_string.encode()).decode('utf-8')
        return encoded_password, timestamp
    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate an STK push request to the customer's phone
        
        Args:
            phone_number (str): Customer's phone number (format: 254XXXXXXXXX)
            amount (float): Amount to charge
            account_reference (str): Account reference for the transaction
            transaction_desc (str): Description of the transaction
            
        Returns:
            dict: Response from M-Pesa API
        """
        try:
            # Get access token if not already obtained
            if not self.access_token:
                self.get_access_token()
                
            if not self.access_token:
                return {"error": "Could not get access token"}
                
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Format phone number (remove leading 0 if exists and ensure it starts with 254)
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
                
            # Ensure phone number has country code
            if not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            # API endpoint for STK Push
            url = f"{self.api_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),  # Convert to integer
                "PartyA": int(phone_number),  # Convert to integer
                "PartyB": self.business_shortcode,
                "PhoneNumber": int(phone_number),  # Convert to integer
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            response = requests.post(url, headers=headers, json=payload)
            return response.json()
            
        except Exception as e:
            logger.error(f"Error initiating STK push: {str(e)}")
            return {"error": str(e)}
    
    def check_transaction_status(self, checkout_request_id):
        """
        Check the status of an STK push transaction
        
        Args:
            checkout_request_id (str): Checkout request ID from the STK push response
            
        Returns:
            dict: Transaction status response
        """
        try:
            # Get access token if not already obtained
            if not self.access_token:
                self.get_access_token()
                
            if not self.access_token:
                return {"error": "Could not get access token"}
                
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # API endpoint for transaction status check
            url = f"{self.api_url}/mpesa/stkpushquery/v1/query"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }
            
            response = requests.post(url, headers=headers, json=payload)
            return response.json()
            
        except Exception as e:
            logger.error(f"Error checking transaction status: {str(e)}")
            return {"error": str(e)}