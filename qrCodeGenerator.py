import qrcode

# Data for QR Code

OrderQRCode = 'https://www.basicinvite.com/'

qr = qrcode.QRCode(
    version=1,
    box_size=10,
    border=5)

qr.add_data(OrderQRCode)
qr.make(fit=True)

img=qr.make_image(fill='black', back_color='white')
img.save('/Users/Trevor/Desktop/basic_invite_qr_code.png')