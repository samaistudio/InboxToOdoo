"""Builds the e-invoice and scan test files in test/invoices/:
  inv-09.xml  XRechnung (UBL syntax) from Werkzeugtechnik Nord for order P00007
  inv-10.pdf  ZUGFeRD-style PDF (visible invoice + embedded CII XML) from Lichtwerk for P00008, price above the order
  inv-11.pdf  scanned paper invoice (image only, slightly rotated and noisy) from Weber for P00009
Simplified test documents: structurally like the standards, not validated against their full rule sets.
Run: python3 test/make_einvoices.py   (needs Chrome, ffmpeg and the docreader container for the PDF attachment step;
set CHROME to Chrome's path if it is not the macOS default; the scan step uses macOS `sips`)"""
import base64
import os
import subprocess
import tempfile
from pathlib import Path

D = Path(__file__).parent / "invoices"
ROOT = Path(__file__).parent.parent


def iban_de(blz, account):
    bban = f"{blz}{account:010d}"
    num = int("".join(str(int(c, 36)) for c in bban + "DE00"))
    return f"DE{98 - num % 97:02d}{bban}"


# ---- inv-09: XRechnung, UBL
UBL = f"""<?xml version="1.0" encoding="UTF-8"?>
<ubl:Invoice xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
 <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</cbc:CustomizationID>
 <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
 <cbc:ID>RE-2026-1219</cbc:ID>
 <cbc:IssueDate>2026-11-24</cbc:IssueDate>
 <cbc:DueDate>2026-12-08</cbc:DueDate>
 <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
 <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
 <cbc:BuyerReference>RW-4410</cbc:BuyerReference>
 <cac:OrderReference><cbc:ID>P00007</cbc:ID></cac:OrderReference>
 <cac:AccountingSupplierParty><cac:Party>
  <cbc:EndpointID schemeID="EM">rechnung@werkzeugtechnik-nord.example</cbc:EndpointID>
  <cac:PartyName><cbc:Name>Werkzeugtechnik Nord GmbH</cbc:Name></cac:PartyName>
  <cac:PostalAddress><cbc:StreetName>Hafenstraße 12</cbc:StreetName><cbc:CityName>Hamburg</cbc:CityName><cbc:PostalZone>20457</cbc:PostalZone><cac:Country><cbc:IdentificationCode>DE</cbc:IdentificationCode></cac:Country></cac:PostalAddress>
  <cac:PartyTaxScheme><cbc:CompanyID>DE298765435</cbc:CompanyID><cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:PartyTaxScheme>
  <cac:PartyLegalEntity><cbc:RegistrationName>Werkzeugtechnik Nord GmbH</cbc:RegistrationName></cac:PartyLegalEntity>
 </cac:Party></cac:AccountingSupplierParty>
 <cac:AccountingCustomerParty><cac:Party>
  <cbc:EndpointID schemeID="EM">rechnungen@rheinmark-handel.example</cbc:EndpointID>
  <cac:PostalAddress><cbc:StreetName>Industriestraße 7</cbc:StreetName><cbc:CityName>Köln</cbc:CityName><cbc:PostalZone>50735</cbc:PostalZone><cac:Country><cbc:IdentificationCode>DE</cbc:IdentificationCode></cac:Country></cac:PostalAddress>
  <cac:PartyLegalEntity><cbc:RegistrationName>Rheinmark Handels GmbH</cbc:RegistrationName></cac:PartyLegalEntity>
 </cac:Party></cac:AccountingCustomerParty>
 <cac:PaymentMeans><cbc:PaymentMeansCode>58</cbc:PaymentMeansCode><cac:PayeeFinancialAccount><cbc:ID>{iban_de("99020050", 1234567)}</cbc:ID></cac:PayeeFinancialAccount></cac:PaymentMeans>
 <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">61.56</cbc:TaxAmount>
  <cac:TaxSubtotal><cbc:TaxableAmount currencyID="EUR">324.00</cbc:TaxableAmount><cbc:TaxAmount currencyID="EUR">61.56</cbc:TaxAmount>
   <cac:TaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19</cbc:Percent><cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:TaxCategory></cac:TaxSubtotal>
 </cac:TaxTotal>
 <cac:LegalMonetaryTotal><cbc:LineExtensionAmount currencyID="EUR">324.00</cbc:LineExtensionAmount><cbc:TaxExclusiveAmount currencyID="EUR">324.00</cbc:TaxExclusiveAmount>
  <cbc:TaxInclusiveAmount currencyID="EUR">385.56</cbc:TaxInclusiveAmount><cbc:PayableAmount currencyID="EUR">385.56</cbc:PayableAmount></cac:LegalMonetaryTotal>
 <cac:InvoiceLine><cbc:ID>1</cbc:ID><cbc:InvoicedQuantity unitCode="H87">6</cbc:InvoicedQuantity><cbc:LineExtensionAmount currencyID="EUR">324.00</cbc:LineExtensionAmount>
  <cac:Item><cbc:Name>Winkelschleifer WS-125</cbc:Name><cac:SellersItemIdentification><cbc:ID>WS-125</cbc:ID></cac:SellersItemIdentification>
   <cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19</cbc:Percent><cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:ClassifiedTaxCategory></cac:Item>
  <cac:Price><cbc:PriceAmount currencyID="EUR">54.00</cbc:PriceAmount></cac:Price></cac:InvoiceLine>
</ubl:Invoice>
"""
(D / "inv-09.xml").write_text(UBL, encoding="utf-8")
print("inv-09.xml XRechnung (UBL)")

# ---- inv-10: ZUGFeRD-style PDF with embedded CII XML (LM-50 at 73.00 instead of 71.00)
CII = f"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
 xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
 <rsm:ExchangedDocumentContext><ram:GuidelineSpecifiedDocumentContextParameter><ram:ID>urn:cen.eu:en16931:2017</ram:ID></ram:GuidelineSpecifiedDocumentContextParameter></rsm:ExchangedDocumentContext>
 <rsm:ExchangedDocument><ram:ID>LW-50340</ram:ID><ram:TypeCode>380</ram:TypeCode><ram:IssueDateTime><udt:DateTimeString format="102">20261124</udt:DateTimeString></ram:IssueDateTime></rsm:ExchangedDocument>
 <rsm:SupplyChainTradeTransaction>
  <ram:IncludedSupplyChainTradeLineItem>
   <ram:AssociatedDocumentLineDocument><ram:LineID>1</ram:LineID></ram:AssociatedDocumentLineDocument>
   <ram:SpecifiedTradeProduct><ram:SellerAssignedID>LM-50</ram:SellerAssignedID><ram:Name>Laser-Entfernungsmesser LM-50</ram:Name></ram:SpecifiedTradeProduct>
   <ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>73.00</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement>
   <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="H87">4</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
   <ram:SpecifiedLineTradeSettlement><ram:ApplicableTradeTax><ram:TypeCode>VAT</ram:TypeCode><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>19</ram:RateApplicablePercent></ram:ApplicableTradeTax>
    <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>292.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement>
  </ram:IncludedSupplyChainTradeLineItem>
  <ram:ApplicableHeaderTradeAgreement>
   <ram:SellerTradeParty><ram:Name>Lichtwerk Elektro AG</ram:Name>
    <ram:PostalTradeAddress><ram:PostcodeCode>80802</ram:PostcodeCode><ram:LineOne>Leopoldstraße 88</ram:LineOne><ram:CityName>München</ram:CityName><ram:CountryID>DE</ram:CountryID></ram:PostalTradeAddress>
    <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE314159262</ram:ID></ram:SpecifiedTaxRegistration></ram:SellerTradeParty>
   <ram:BuyerTradeParty><ram:Name>Rheinmark Handels GmbH</ram:Name><ram:PostalTradeAddress><ram:PostcodeCode>50735</ram:PostcodeCode><ram:LineOne>Industriestraße 7</ram:LineOne><ram:CityName>Köln</ram:CityName><ram:CountryID>DE</ram:CountryID></ram:PostalTradeAddress></ram:BuyerTradeParty>
   <ram:BuyerOrderReferencedDocument><ram:IssuerAssignedID>P00008</ram:IssuerAssignedID></ram:BuyerOrderReferencedDocument>
  </ram:ApplicableHeaderTradeAgreement>
  <ram:ApplicableHeaderTradeDelivery/>
  <ram:ApplicableHeaderTradeSettlement>
   <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
   <ram:SpecifiedTradeSettlementPaymentMeans><ram:TypeCode>58</ram:TypeCode><ram:PayeePartyCreditorFinancialAccount><ram:IBANID>{iban_de("99070150", 7654321)}</ram:IBANID></ram:PayeePartyCreditorFinancialAccount></ram:SpecifiedTradeSettlementPaymentMeans>
   <ram:ApplicableTradeTax><ram:CalculatedAmount>55.48</ram:CalculatedAmount><ram:TypeCode>VAT</ram:TypeCode><ram:BasisAmount>292.00</ram:BasisAmount><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>19</ram:RateApplicablePercent></ram:ApplicableTradeTax>
   <ram:SpecifiedTradePaymentTerms><ram:DueDateDateTime><udt:DateTimeString format="102">20261224</udt:DateTimeString></ram:DueDateDateTime></ram:SpecifiedTradePaymentTerms>
   <ram:SpecifiedTradeSettlementHeaderMonetarySummation><ram:LineTotalAmount>292.00</ram:LineTotalAmount><ram:TaxBasisTotalAmount>292.00</ram:TaxBasisTotalAmount>
    <ram:TaxTotalAmount currencyID="EUR">55.48</ram:TaxTotalAmount><ram:GrandTotalAmount>347.48</ram:GrandTotalAmount><ram:DuePayableAmount>347.48</ram:DuePayableAmount></ram:SpecifiedTradeSettlementHeaderMonetarySummation>
  </ram:ApplicableHeaderTradeSettlement>
 </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
"""
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    html = """<!doctype html><html lang=de><head><meta charset=utf-8><style>body{font-family:Georgia,serif;font-size:10.5pt;margin:20mm 22mm}
.top{display:flex;justify-content:space-between;border-bottom:2px solid #111;padding-bottom:4mm}.logo{font-size:18pt;font-style:italic}
table{width:100%;border-collapse:collapse;margin-top:6mm}th{border-bottom:1px solid #111;text-align:left;padding:4px}td{padding:4px}.r{text-align:right}</style></head><body>
<div class=top><div><div class=logo>Lichtwerk Elektro AG</div>Leopoldstraße 88 · 80802 München</div><div style="text-align:right">Rechnungsnr.: <b>LW-50340</b><br>Rechnungsdatum: 24.11.2026<br>Ihre Bestellung: P00008</div></div>
<p style="margin-top:10mm">Rheinmark Handels GmbH<br>Industriestraße 7<br>50735 Köln</p><h1 style="font-size:16pt;letter-spacing:.2em">RECHNUNG</h1>
<p>Diese Rechnung enthält die Rechnungsdaten zusätzlich als ZUGFeRD-Datei (factur-x.xml).</p>
<table><tr><th>Art.-Nr.</th><th>Bezeichnung</th><th class=r>Menge</th><th class=r>Einzelpreis</th><th class=r>Gesamt</th></tr>
<tr><td>LM-50</td><td>Laser-Entfernungsmesser LM-50</td><td class=r>4</td><td class=r>73,00 €</td><td class=r>292,00 €</td></tr></table>
<p style="text-align:right;margin-top:5mm">Netto 292,00 € · USt. 19 % 55,48 € · <b>Gesamt 347,48 €</b></p>
<p>Zahlbar bis 24.12.2026. IBAN DE50 9907 0150 0007 6543 21 · USt-IdNr. DE314159262</p><p style="font-size:8.5pt;color:#555">Alle Angaben fiktiv, Testdokument.</p></body></html>"""
    (t / "z.html").write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={t / 'z.pdf'}", (t / "z.html").as_uri()], stderr=subprocess.DEVNULL, check=True)
    attach = ("import sys,io,base64;from pypdf import PdfReader,PdfWriter;w=PdfWriter(clone_from=PdfReader(io.BytesIO(sys.stdin.buffer.read())));"
              f"w.add_attachment('factur-x.xml',base64.b64decode('{base64.b64encode(CII.encode()).decode()}'));o=io.BytesIO();w.write(o);sys.stdout.buffer.write(o.getvalue())")
    out = subprocess.run(["docker", "compose", "exec", "-T", "docreader", "python", "-c", attach], input=(t / "z.pdf").read_bytes(), capture_output=True, cwd=ROOT, check=True).stdout
    (D / "inv-10.pdf").write_bytes(out)
print("inv-10.pdf ZUGFeRD-style (PDF + factur-x.xml)")

# ---- inv-11: scanned paper invoice (image only)
with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    html = """<!doctype html><html lang=de><head><meta charset=utf-8><style>body{font-family:Helvetica,Arial,sans-serif;font-size:11pt;color:#222;margin:18mm}
.top{display:flex;justify-content:space-between;background:#eee;padding:5mm}.logo{font-size:15pt;font-weight:700}table{width:100%;border-collapse:collapse;margin-top:5mm}
th,td{border:1px solid #999;padding:5px}.r{text-align:right}</style></head><body>
<div class=top><div><div class=logo>Schutzausrüstung Weber KG</div>Industrieweg 5 · 44147 Dortmund</div><div style="text-align:right">Rechnungsnr.: 2026/4519<br>Datum: 24.11.2026<br>Ihre Bestellung: P00009</div></div>
<p style="margin-top:8mm">Rheinmark Handels GmbH<br>Industriestraße 7<br>50735 Köln</p><h2>Rechnung</h2>
<table><tr><th>Pos.</th><th>Art.-Nr.</th><th>Bezeichnung</th><th class=r>Menge</th><th class=r>Einzelpreis</th><th class=r>Gesamt</th></tr>
<tr><td>1</td><td>WK-PRO</td><td>Werkzeugkoffer Pro</td><td class=r>12</td><td class=r>31,00 €</td><td class=r>372,00 €</td></tr></table>
<p style="text-align:right">Nettobetrag 372,00 €<br>zzgl. 19 % USt. 70,68 €<br><b>Rechnungsbetrag 442,68 €</b></p>
<p>Zahlbar bis 08.12.2026.</p><p style="font-size:9pt">USt-IdNr. DE271828180 · IBAN DE57 9904 4050 0005 5501 23 · Alle Angaben fiktiv, Testdokument.</p></body></html>"""
    (t / "s.html").write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--force-device-scale-factor=2", "--window-size=1240,1754",
                    f"--screenshot={t / 's.png'}", (t / "s.html").as_uri()], stderr=subprocess.DEVNULL, check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(t / "s.png"), "-vf",
                    "rotate=0.9*PI/180:fillcolor=white:ow=iw:oh=ih,noise=alls=10:allf=t,format=gray,eq=contrast=1.1",
                    str(t / "scan.jpg")], check=True)
    subprocess.run(["sips", "-s", "format", "pdf", str(t / "scan.jpg"), "--out", str(D / "inv-11.pdf")], capture_output=True, check=True)
print("inv-11.pdf scanned (image only)")
