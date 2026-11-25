// Node "Neue Rechnungen": unread mails with an attachment to the invoice mailbox, oldest first.
const s = $('Einstellungen').first().json.data;
const box = (s.inv_mailbox || 'rechnungen@rheinmark-handel.example').toLowerCase();
return ($json.messages || [])
  .filter(m => !m.Read && (m.To || []).some(t => t.Address.toLowerCase() === box) && m.Attachments > 0)
  .sort((a, b) => String(a.Created).localeCompare(String(b.Created)))
  .map(m => ({ json: { ID: m.ID, MessageID: m.MessageID } }));
