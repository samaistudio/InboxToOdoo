// Node "PDF-Anhänge": one item per invoice file (PDF, XML or image) in the new mails.
const isDoc = a => /(pdf|xml|png|jpe?g|tiff?)$/i.test(a.ContentType) || /\.(pdf|xml|png|jpe?g|tiff?)$/i.test(a.FileName);
return $input.all().flatMap(({ json: m }) =>
  (m.Attachments || []).filter(isDoc).map(a => ({
    json: {
      message_id: m.MessageID, mailpit_id: m.ID, part_id: a.PartID, filename: a.FileName,
      from_email: m.From.Address, from_name: m.From.Name, subject: m.Subject, text: m.Text,
    },
  })),
);
