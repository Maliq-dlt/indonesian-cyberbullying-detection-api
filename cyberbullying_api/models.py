import ipaddress
import re
import socket
import urllib.parse

from pydantic import BaseModel, Field, field_validator


def check_ssrf_url(url: str, allowed_domains: list[str]) -> str:
    # Harus menggunakan HTTP atau HTTPS
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("URL harus dimulai dengan http:// atau https://")

    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URL tidak memiliki domain yang valid")

        # Periksa whitelist domain (harus berupa domain itu sendiri atau submainnya)
        domain_ok = any(
            hostname.lower() == domain or hostname.lower().endswith("." + domain) for domain in allowed_domains
        )
        if not domain_ok:
            raise ValueError(f"Domain harus berupa atau subdomain dari: {', '.join(allowed_domains)}")

        # Cek apakah hostname adalah IP address
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_loopback or ip.is_private or ip.is_link_local:
                raise ValueError("URL tidak boleh merujuk ke alamat IP lokal/privat")
        except ValueError:
            # Jika bukan IP address, pastikan bukan hostname lokal
            if hostname.lower() in ["localhost", "127.0.0.1", "0.0.0.0"]:
                raise ValueError("URL tidak boleh merujuk ke alamat lokal")

            # Filter ekspresi reguler untuk mendeteksi IP privat secara literal
            private_ip_patterns = [
                r"^127\.",
                r"^10\.",
                r"^192\.168\.",
                r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
                r"^169\.254\.",
            ]
            for pattern in private_ip_patterns:
                if re.match(pattern, hostname):
                    raise ValueError("URL tidak boleh merujuk ke alamat IP lokal/privat")

            # Resolusi DNS untuk memverifikasi IP aktual hostname
            try:
                addr_info = socket.getaddrinfo(hostname, None, family=socket.AF_INET)
                for addr in addr_info:
                    resolved_ip = ipaddress.ip_address(addr[4][0])
                    if (
                        resolved_ip.is_loopback
                        or resolved_ip.is_private
                        or resolved_ip.is_link_local
                        or resolved_ip.is_reserved
                    ):
                        raise ValueError("URL tidak boleh merujuk ke alamat IP lokal/privat (terdeteksi via DNS)")
            except socket.gaierror:
                raise ValueError("Gagal melakukan resolusi DNS untuk hostname")
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f"Format URL tidak valid: {str(e)}")

    return url


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    use_fuzzy: bool | None = False  # Dinonaktifkan secara default untuk performa maksimal


class LexiconMatch(BaseModel):
    matched_phrase: str
    category: str
    severity: str
    method: str


class LexiconResponse(BaseModel):
    text: str
    normalized_spaced: str
    normalized_compact: str
    is_cyberbullying: bool
    risk_label: str
    score: int
    matches: list[LexiconMatch]
    execution_time: float | None = 0.0


class WordImportance(BaseModel):
    word: str
    weight_toxic: float
    weight_bully: float


class MLResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str
    word_importances: list[WordImportance] = []
    execution_time: float | None = 0.0


class TransformerResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str
    word_importances: list[WordImportance] = []
    execution_time: float | None = 0.0


class EnsembleResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str
    word_importances: list[WordImportance] = []
    execution_time: float | None = 0.0


class HybridResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str
    decision_source: str
    reason: str
    word_importances: list[WordImportance] = []
    execution_time: float | None = 0.0


class BatchTextRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=50)
    model_name: str | None = "llama3.2:3b"

    @field_validator("texts")
    @classmethod
    def validate_texts_length(cls, v: list[str]) -> list[str]:
        if len(v) > 50:
            raise ValueError("Maksimal jumlah teks dalam batch adalah 50")
        if len(v) < 1:
            raise ValueError("Minimal harus ada 1 teks dalam batch")
        return v


class BatchItemResponse(BaseModel):
    text: str
    is_toxic: bool
    is_bully: bool
    probability_toxic: float
    probability_bully: float
    category: str
    decision_source: str
    reason: str
    word_importances: list[WordImportance] = []


class BatchResponse(BaseModel):
    results: list[BatchItemResponse]


def determine_category(is_toxic: bool, is_bully: bool) -> str:
    if is_toxic and is_bully:
        return "Bully-toxic(bully)"
    elif not is_toxic and is_bully:
        return "non-Toxic Bully(Sarkasme)"
    elif is_toxic and not is_bully:
        return "Toxic non-bully(slang)"
    else:
        return "non-toxic non-bully(Normal)"


class ScrapeTikTokRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=500)
    max_comments: int | None = Field(20, ge=1, le=100)

    @field_validator("url")
    @classmethod
    def validate_tiktok_url(cls, v: str) -> str:
        return check_ssrf_url(v, ["tiktok.com"])


class ScrapeXRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=500)
    max_tweets: int | None = Field(20, ge=1, le=100)

    @field_validator("url")
    @classmethod
    def validate_x_url(cls, v: str) -> str:
        return check_ssrf_url(v, ["x.com", "twitter.com"])


class ScrapeResponse(BaseModel):
    success: bool
    count: int
    data: list[str]


class ReallocateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    new_is_toxic: bool
    new_is_bully: bool


class ReallocateResponse(BaseModel):
    success: bool
    message: str


class UpdateCookiesRequest(BaseModel):
    platform: str
    cookies: list[dict]


class BulkReallocateItem(BaseModel):
    text: str = Field(..., min_length=1)
    new_is_toxic: bool
    new_is_bully: bool


class BulkReallocateRequest(BaseModel):
    items: list[BulkReallocateItem]
