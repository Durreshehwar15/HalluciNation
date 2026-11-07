// Simulated pipeline. Each stage lasts STAGE_MS so you can watch it progress.
export const STAGE_MS = 4000
export const STATUSES = [
  'submitted', 'triage', 'investigating', 'fixing', 'testing', 'review', 'awaiting_approval',
]

// `at` = index of the stage when the event appears
export const EVENTS = [
  { at: 1, agent: 'Triage Agent', message: 'Feature affected: checkout / coupons. Reproduced from report. Created investigation task for Code Investigation Agent.' },
  { at: 2, agent: 'Code Investigation Agent', message: 'Root cause: apply_coupon() assumes the coupon lookup always returns an object. An invalid code returns None, causing AttributeError.', evidence: 'payments/coupons.py:42  |  logs: AttributeError: NoneType has no attribute discount' },
  { at: 3, agent: 'Fix Agent', message: 'Proposed patch: validate the coupon before use and raise a friendly InvalidCouponError. Handed off to Testing Agent.', evidence: 'patch: payments/coupons.py (+6 -1)' },
  { at: 4, agent: 'Testing Agent', message: 'Ran tests in Docker sandbox. New regression test passes; 24/24 existing tests still pass.', evidence: 'pytest: 25 passed, 0 failed' },
  { at: 5, agent: 'Reviewer Agent', message: 'Approved. Fix is minimal, test evidence is sufficient, no side effects found in the checkout flow.' },
  { at: 6, agent: 'Switch', message: 'All agents agree. Waiting for human approval before any PR is created.' },
]

export const PATCH = {
  file: 'payments/coupons.py',
  diff: `--- a/payments/coupons.py
+++ b/payments/coupons.py
@@ -38,7 +38,12 @@ def apply_coupon(cart, code):
-    coupon = Coupon.lookup(code)
-    cart.total -= coupon.discount
+    coupon = Coupon.lookup(code)
+    if coupon is None:
+        raise InvalidCouponError(f"Coupon '{code}' is not valid")
+    cart.total -= coupon.discount
     return cart`,
}

export const TESTS = {
  passed: 25, failed: 0, total: 25,
  cases: [
    { name: 'test_invalid_coupon_returns_error (new)', status: 'passed' },
    { name: 'test_valid_coupon_applies_discount', status: 'passed' },
    { name: 'test_expired_coupon_rejected', status: 'passed' },
    { name: 'test_checkout_total', status: 'passed' },
  ],
}

export const REVIEW = {
  verdict: 'approved',
  comments: ['Minimal change, scoped to coupon handling.', 'Regression test covers the reported crash.', 'No existing tests broken.'],
}
