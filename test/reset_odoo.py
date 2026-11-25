# odoo shell: remove everything the complaint workflow created (drafts, cancelled records, notes).
env = env  # noqa: F821
so = env["sale.order"].search([("client_order_ref", "like", "Ersatz zu %")])
for o in so:
    if o.state not in ("draft", "cancel"):
        o._action_cancel()
so.unlink()
mv = env["account.move"].search([("move_type", "=", "out_refund"), ("ref", "like", "Reklamation %")])
# Credit notes that were ever posted stay (accounting audit trail); they are reset and cancelled instead.
kept = mv.filtered(lambda m: m.state == "posted" or (m.name and m.name != "/"))
for m in kept:
    if m.state == "posted":
        m.button_draft()
    if m.state != "cancel":
        m.button_cancel()
(mv - kept).unlink()
msgs = env["mail.message"].search([("model", "=", "sale.order"), ("body", "ilike", "Reklamation test-")])
msgs.unlink()
bills = env["account.move"].search([("move_type", "=", "in_invoice"), ("narration", "ilike", "Automatisch erfasst")])
posted = bills.filtered(lambda m: m.name and m.name != "/")
for m in posted:
    if m.state == "posted":
        m.button_draft()
    if m.state != "cancel":
        m.button_cancel()
(bills - posted).unlink()
inv_msgs = env["mail.message"].search([("body", "ilike", "Eingangsrechnung "), ("model", "!=", "account.move")])
inv_msgs.unlink()
env.cr.commit()
print("invoices:", len(bills - posted), "drafts removed,", len(posted), "posted bills cancelled (audit trail),", len(inv_msgs), "notes")
print("removed", len(so), "orders,", len(mv - kept), "credit notes (" + str(len(kept)), "cancelled, kept for the audit trail),", len(msgs), "notes")
