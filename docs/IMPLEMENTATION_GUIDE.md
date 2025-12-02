# Cost Melt - Implementation Guide

**Complete guide for implementing Cost Melt incrementally**

---

## Quick Start

This guide helps you implement Cost Melt features incrementally, following best practices and maintaining production quality.

---

## Current Status

### ✅ Phase 1: MVP Core Platform (COMPLETE)

All core optimization features are implemented and production-ready:

- ✅ Smart Model Routing
- ✅ Semantic Caching
- ✅ Prompt Compression
- ✅ Micro-Batching
- ✅ Cost Analytics Dashboard
- ✅ Authentication & Security
- ✅ Landing Page
- ✅ Client SDKs
- ✅ Documentation

**You can start using Cost Melt immediately!**

---

## Next Steps: Phase 2 - Billing & Subscriptions

### Step-by-Step Implementation

#### Step 1: Database Schema (2 days)

**File**: `backend/db/migrations/002_billing.sql`

```sql
-- Run this migration in Supabase SQL Editor

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    plan_id TEXT NOT NULL CHECK (plan_id IN ('free', 'pro', 'enterprise')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'canceled', 'past_due', 'trialing')),
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end TIMESTAMPTZ NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe_subscription_id ON subscriptions(stripe_subscription_id);

-- Billing events table
CREATE TABLE IF NOT EXISTS billing_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    subscription_id UUID REFERENCES subscriptions(id),
    event_type TEXT NOT NULL CHECK (event_type IN ('usage', 'overage', 'subscription_change', 'payment', 'refund')),
    amount DECIMAL(10, 2) NOT NULL,
    currency TEXT DEFAULT 'usd',
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_billing_events_user_id ON billing_events(user_id);
CREATE INDEX idx_billing_events_subscription_id ON billing_events(subscription_id);
CREATE INDEX idx_billing_events_created_at ON billing_events(created_at);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    subscription_id UUID REFERENCES subscriptions(id),
    stripe_invoice_id TEXT UNIQUE,
    stripe_charge_id TEXT,
    amount DECIMAL(10, 2) NOT NULL,
    currency TEXT DEFAULT 'usd',
    status TEXT NOT NULL CHECK (status IN ('draft', 'open', 'paid', 'void', 'uncollectible')),
    invoice_pdf_url TEXT,
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);

CREATE INDEX idx_invoices_user_id ON invoices(user_id);
CREATE INDEX idx_invoices_stripe_invoice_id ON invoices(stripe_invoice_id);

-- Payment methods table
CREATE TABLE IF NOT EXISTS payment_methods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    stripe_payment_method_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    type TEXT NOT NULL CHECK (type IN ('card')),
    card_last4 TEXT,
    card_brand TEXT,
    card_exp_month INT,
    card_exp_year INT,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payment_methods_user_id ON payment_methods(user_id);
CREATE INDEX idx_payment_methods_stripe_payment_method_id ON payment_methods(stripe_payment_method_id);
```

**Action Items**:
1. Copy SQL above
2. Open Supabase SQL Editor
3. Paste and run
4. Verify tables created

#### Step 2: Stripe Integration (5 days)

**Install Dependencies**:

```bash
cd backend
pip install stripe
```

**Create Stripe Client** (`backend/services/stripe_client.py`):

```python
import stripe
from typing import Optional, Dict, Any
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeClient:
    async def create_customer(self, email: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a Stripe customer"""
        customer = stripe.Customer.create(
            email=email,
            name=name,
        )
        return customer
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a Stripe subscription"""
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
        )
        return subscription
    
    async def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> Dict[str, Any]:
        """Update subscription to new plan"""
        subscription = stripe.Subscription.retrieve(subscription_id)
        updated = stripe.Subscription.modify(
            subscription_id,
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": new_price_id,
            }],
            proration_behavior="create_prorations",
        )
        return updated
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True
    ) -> Dict[str, Any]:
        """Cancel subscription"""
        if cancel_at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True,
            )
        else:
            subscription = stripe.Subscription.delete(subscription_id)
        return subscription
    
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> stripe.Event:
        """Verify Stripe webhook signature"""
        return stripe.Webhook.construct_event(
            payload, signature, secret
        )
```

**Create Billing API** (`backend/api/billing.py`):

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.stripe_client import StripeClient
from security.rbac import require_role

router = APIRouter(prefix="/billing", tags=["billing"])
stripe_client = StripeClient()

class CreateSubscriptionRequest(BaseModel):
    plan_id: str  # 'pro' or 'enterprise'
    payment_method_id: Optional[str] = None

@router.post("/subscriptions")
async def create_subscription(
    request: CreateSubscriptionRequest,
    user_id: str = Depends(require_role("write"))
):
    """Create a new subscription"""
    # Implementation here
    pass

@router.get("/subscriptions")
async def get_subscription(
    user_id: str = Depends(require_role("read"))
):
    """Get current subscription"""
    # Implementation here
    pass

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    try:
        event = stripe_client.verify_webhook_signature(
            payload,
            signature,
            os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle event
    if event["type"] == "customer.subscription.created":
        # Update database
        pass
    elif event["type"] == "customer.subscription.updated":
        # Update database
        pass
    elif event["type"] == "invoice.paid":
        # Record payment
        pass
    
    return {"status": "success"}
```

**Action Items**:
1. Get Stripe API keys from https://dashboard.stripe.com
2. Add `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` to `.env`
3. Create Stripe products and prices
4. Implement billing API endpoints
5. Test webhook locally with Stripe CLI

#### Step 3: Usage Tracking (4 days)

**Create Billing Service** (`backend/services/billing_service.py`):

```python
from datetime import datetime, timedelta
from db.supabase_client import get_supabase
from utils.cost_calculator import CostCalculator

class BillingService:
    def __init__(self):
        self.supabase = get_supabase()
        self.cost_calculator = CostCalculator()
    
    async def track_usage(self, user_id: str, request_data: dict):
        """Track API usage for billing"""
        # Get current subscription
        subscription = self.get_active_subscription(user_id)
        
        # Get current period usage
        period_start = subscription["current_period_start"]
        period_end = subscription["current_period_end"]
        
        # Count requests in period
        usage = self.count_requests(user_id, period_start, period_end)
        
        # Check against plan limits
        plan = self.get_plan(subscription["plan_id"])
        
        if usage["requests"] > plan["request_limit"]:
            # Calculate overage
            overage = usage["requests"] - plan["request_limit"]
            await self.charge_overage(user_id, overage, subscription["id"])
    
    def count_requests(self, user_id: str, start: datetime, end: datetime) -> dict:
        """Count requests in period"""
        result = self.supabase.table("requests").select("*").eq(
            "user_id", user_id
        ).gte("created_at", start.isoformat()).lte(
            "created_at", end.isoformat()
        ).execute()
        
        total_requests = len(result.data)
        total_tokens_in = sum(r["tokens_in"] for r in result.data)
        total_tokens_out = sum(r["tokens_out"] for r in result.data)
        total_cost = sum(r["actual_cost"] for r in result.data)
        
        return {
            "requests": total_requests,
            "tokens_in": total_tokens_in,
            "tokens_out": total_tokens_out,
            "cost": total_cost,
        }
    
    def get_plan(self, plan_id: str) -> dict:
        """Get plan details"""
        plans = {
            "free": {
                "request_limit": 5000,
                "price": 0,
            },
            "pro": {
                "request_limit": 250000,
                "price": 49,
            },
            "enterprise": {
                "request_limit": -1,  # Unlimited
                "price": -1,  # Custom
            },
        }
        return plans.get(plan_id, plans["free"])
```

**Action Items**:
1. Implement usage tracking in gateway
2. Create billing worker (daily cron)
3. Test usage calculation
4. Test overage charging

#### Step 4: Billing Dashboard (5 days)

**Create Billing Page** (`dashboard/app/billing/page.tsx`):

```typescript
'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/Card';
import { Metric } from '@/components/Metric';

export default function BillingPage() {
  const [subscription, setSubscription] = useState(null);
  const [usage, setUsage] = useState(null);

  useEffect(() => {
    // Fetch subscription and usage
    fetch('/api/billing/subscription')
      .then(res => res.json())
      .then(data => setSubscription(data));
    
    fetch('/api/billing/usage')
      .then(res => res.json())
      .then(data => setUsage(data));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Billing & Subscription</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Current Plan">
          <Metric label="Plan" value={subscription?.plan_id} />
          <Metric label="Status" value={subscription?.status} />
          <Metric label="Period End" value={subscription?.current_period_end} />
        </Card>
        
        <Card title="Usage This Period">
          <Metric label="Requests" value={usage?.requests} />
          <Metric label="Limit" value={subscription?.plan_limit} />
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full" 
                style={{ width: `${(usage?.requests / subscription?.plan_limit) * 100}%` }}
              />
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
```

**Action Items**:
1. Create billing API routes in dashboard
2. Build billing UI components
3. Add Stripe Checkout integration
4. Test subscription flow
5. Add invoice download

---

## Implementation Checklist

### Phase 2: Billing & Subscriptions

- [ ] **Database Schema**
  - [ ] Create subscriptions table
  - [ ] Create billing_events table
  - [ ] Create invoices table
  - [ ] Create payment_methods table
  - [ ] Run migrations

- [ ] **Stripe Integration**
  - [ ] Install Stripe SDK
  - [ ] Create Stripe client
  - [ ] Implement subscription creation
  - [ ] Implement subscription updates
  - [ ] Implement webhook handler
  - [ ] Test webhooks

- [ ] **Usage Tracking**
  - [ ] Track requests per user
  - [ ] Calculate usage vs. limits
  - [ ] Calculate overage charges
  - [ ] Create billing worker
  - [ ] Test billing calculations

- [ ] **Billing API**
  - [ ] POST /billing/subscriptions
  - [ ] GET /billing/subscriptions
  - [ ] PUT /billing/subscriptions
  - [ ] DELETE /billing/subscriptions
  - [ ] GET /billing/usage
  - [ ] GET /billing/invoices
  - [ ] POST /billing/webhooks/stripe

- [ ] **Billing Dashboard**
  - [ ] Create billing page
  - [ ] Display current plan
  - [ ] Display usage meters
  - [ ] Add payment method management
  - [ ] Add subscription upgrade/downgrade
  - [ ] Add invoice downloads

- [ ] **Rate Limiting by Tier**
  - [ ] Update rate limit middleware
  - [ ] Implement tier-based limits
  - [ ] Test rate limiting

### Phase 3: User Onboarding

- [ ] **Authentication**
  - [ ] User signup flow
  - [ ] User login flow
  - [ ] Email verification
  - [ ] Password reset

- [ ] **Onboarding Wizard**
  - [ ] Welcome screen
  - [ ] API key generation
  - [ ] Integration guide
  - [ ] Test API call
  - [ ] Dashboard tour

- [ ] **Integration Guides**
  - [ ] Python SDK guide
  - [ ] Node.js SDK guide
  - [ ] REST API guide

---

## Testing Strategy

### Unit Tests

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd dashboard
npm test
```

### Integration Tests

```bash
# Test API endpoints
pytest tests/integration/

# Test Stripe webhooks
stripe listen --forward-to localhost:8000/billing/webhooks/stripe
```

### E2E Tests

```bash
# Test full user flow
npm run test:e2e
```

---

## Deployment Checklist

Before deploying to production:

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Stripe webhook endpoint configured
- [ ] Database migrations run
- [ ] Rate limiting tested
- [ ] Monitoring set up
- [ ] Error tracking configured
- [ ] Documentation updated

---

## Resources

- **Architecture**: `docs/ARCHITECTURE.md`
- **PRD**: `docs/PRD.md`
- **Technical Specs**: `docs/TECHNICAL_SPECS.md`
- **Roadmap**: `docs/ROADMAP.md`
- **API Docs**: `docs/API.md`
- **Security**: `docs/SECURITY.md`

---

**Ready to start implementing? Begin with Step 1: Database Schema!**

