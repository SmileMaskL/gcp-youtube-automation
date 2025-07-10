# 멀티스테이지 빌드 적용
FROM python:3.11-bookworm AS builder

# 1. 시스템 패키지 (빌드용) - ExifTool 빌드 관련 패키지 제거
# build-essential, wget, perl은 ExifTool 빌드에 필요했으므로 제거합니다.
RUN apt-get update && apt-get install -y \
    # 필요한 다른 빌드 도구가 있다면 여기에 추가
    # 예: git
    && rm -rf /var/lib/apt/lists/*

# ExifTool 빌드 부분 전체 제거
# ARG EXIFTOOL_VERSION=12.87
# ENV EXIFTOOL_VERSION_BUILD=${EXIFTOOL_VERSION}
# RUN wget "https://exiftool.org/Image-ExifTool-${EXIFTOOL_VERSION_BUILD}.tar.gz" -O /tmp/Image-ExifTool.tar.gz && \
#     mkdir -p /tmp/exiftool_build && \
#     tar -xzf Image-ExifTool.tar.gz -C /tmp/exiftool_build && \
#     cd "/tmp/exiftool_build/Image-ExifTool-${EXIFTOOL_VERSION_BUILD}" && \
#     perl Makefile.PL && \
#     make && make install

# ----------------------------------------
# 런타임 이미지
FROM python:3.11-slim-bookworm

# 3. 런타임 패키지
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 libglib2.0-0 libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# 4. ExifTool 복사 부분 전체 제거
# COPY --from=builder /usr/local/bin/exiftool /usr/local/bin/
# COPY --from=builder /usr/local/share/man/man1/exiftool.1 /usr/local/share/man/man1/

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]
