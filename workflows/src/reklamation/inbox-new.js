// Node "Neue Reklamationen": unread mails to the service mailbox.
const s = $('Einstellungen').first().json.data;
const msgs = ($json.messages || []).filter(m => !m.Read && (m.To || []).some(t => t.Address.toLowerCase() === s.service_email));
return msgs.map(m => ({ json: { ID: m.ID, MessageID: m.MessageID } }));
