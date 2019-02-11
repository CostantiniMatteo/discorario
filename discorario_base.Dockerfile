FROM surnet/alpine-wkhtmltopdf:3.6-0.12.4-small as builder

FROM python:3.7.0-alpine3.7

RUN apk add --no-cache \
  libstdc++ \
  libx11 \
  libxrender \
  libxext \
  libssl1.0 \
  ca-certificates \
  fontconfig \
  freetype \
  ttf-dejavu \
  ttf-droid \
  ttf-freefont \
  ttf-liberation \
  ttf-ubuntu-font-family \
  build-base \
  python3-dev \
  libffi-dev \
  openssl-dev \
  xvfb


COPY --from=builder /bin/wkhtmltopdf /bin/wkhtmltopdf

WORKDIR /usr/discorario
COPY requirements.txt ./

# --virtual .pynacl_deps
# Note it is optional to use the --virtual flag but it makes it easy to
# trim the image because you can run apk del .pynacl_deps later in your
# Dockerfile as they are not needed any more and would reduce
# the overall size of the image.
# RUN apk add --no-cache xvfb build-base python3-dev libffi-dev openssl-dev

RUN pip install --no-cache-dir -r requirements.txt
