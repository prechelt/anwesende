import io

import segno


def qrcode_data(text, imgtype="svg"):
    qr = segno.make(text, error='Q')
    buff = io.BytesIO()
    qr.save(buff, scale=4, kind=imgtype)
    return buff.getvalue()
