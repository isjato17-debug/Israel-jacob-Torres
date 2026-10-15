"""Versioned, deterministic AutoForm definitions and reproducible unsigned documents.

Only structured source is persisted. File bytes are rendered on demand, never stored
in database blobs or exposed through a public bucket. No network/provider activity.
"""
from datetime import date
import hashlib
import html
import json
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

TEMPLATE_KEY = "cleaning_service_agreement"
TEMPLATE_VERSION = 1
TITLE = "Cleaning Service Agreement"
NOTICE = ("English-language unsigned agreement draft, not a government form or legal advice. "
          "Both parties should review it; legal enforceability and local rules need qualified review. "
          "Customer approval is not an electronic signature, submission or authorization to charge.")


class PassportFields(BaseModel):
    model_config = ConfigDict(extra="forbid")
    business_name: str = Field(default="", max_length=160)
    representative_name: str = Field(default="", max_length=160)
    business_email: str = Field(default="", max_length=254)
    municipality: str = Field(default="", max_length=160)

    @field_validator("*", mode="before")
    @classmethod
    def clean(cls, value):
        if isinstance(value, str):
            if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", value):
                raise ValueError("Control characters are not allowed")
            return value.strip()
        return value

    @field_validator("business_email")
    @classmethod
    def email(cls, value):
        if value and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter a business contact email")
        return value


class AgreementFields(PassportFields):
    client_name: str = Field(default="", max_length=160)
    service_address: str = Field(default="", max_length=500)
    service_scope: str = Field(default="", max_length=3000)
    frequency: str = Field(default="", max_length=300)
    price_cents: int | None = Field(default=None, gt=0, le=100_000_000, strict=True)
    payment_terms: str = Field(default="", max_length=1200)
    start_date: str = Field(default="", max_length=10)
    cancellation_terms: str = Field(default="", max_length=1200)
    supplies_terms: str = Field(default="", max_length=1200)

    @field_validator("start_date")
    @classmethod
    def valid_date(cls, value):
        if value:
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError()
            except ValueError:
                raise ValueError("Use a valid YYYY-MM-DD service start date") from None
        return value


LABELS = {
    "business_name": "Business / provider name", "representative_name": "Provider representative",
    "business_email": "Business contact email (optional)", "municipality": "Municipality",
    "client_name": "Customer / client name", "service_address": "Service property address",
    "service_scope": "Included work and explicit exclusions", "frequency": "Service frequency / schedule",
    "price_cents": "Price per service visit (USD)", "payment_terms": "Payment terms",
    "start_date": "First service date", "cancellation_terms": "Cancellation / termination terms",
    "supplies_terms": "Supplies, access and work-site safety arrangements",
}
REQUIRED = tuple(k for k in LABELS if k != "business_email")


def definition():
    props = AgreementFields.model_json_schema()["properties"]
    return {
        "key": TEMPLATE_KEY, "version": TEMPLATE_VERSION, "title": TITLE, "notice": NOTICE,
        "fields": [{"key": k, "label": label, "required": k in REQUIRED,
                    "type": "money" if k == "price_cents" else "date" if k == "start_date"
                    else "textarea" if k in ("service_scope", "supplies_terms", "cancellation_terms", "payment_terms")
                    else "text", "max_length": props[k].get("maxLength")}
                   for k, label in LABELS.items()],
    }


def missing(fields):
    return [key for key in REQUIRED if not fields.get(key)]


def sections(source):
    f = source["fields"]
    price = f["price_cents"]
    return [
        {"heading": "Document status", "body": f"Unsigned draft prepared {source['prepared_at']}. {NOTICE}"},
        {"heading": "Parties", "body": f"Provider: {f['business_name']}, represented by {f['representative_name']}. "
         f"Business contact: {f['business_email'] or 'Not supplied'}. Client: {f['client_name']}."},
        {"heading": "Service location", "body": f"{f['service_address']}. Municipality: {f['municipality']}. "
         f"Planning jurisdiction: {source['jurisdiction']}; confirm actual local obligations."},
        {"heading": "Scope of work and exclusions", "body": f["service_scope"]},
        {"heading": "Service schedule", "body": f"First service date: {f['start_date']}. {f['frequency']}"},
        {"heading": "Price and payment", "body": f"USD ${price // 100:,}.{price % 100:02d} per service visit. "
         f"{f['payment_terms']} Any applicable tax, fees or changed scope must be clarified and agreed before work. "
         "This document does not charge or authorize a payment."},
        {"heading": "Supplies, access and safety", "body": f["supplies_terms"]},
        {"heading": "Cancellation and termination", "body": f["cancellation_terms"]},
        {"heading": "Changes and review", "body": "Changes to scope, price or schedule require both parties' agreement. "
         "Do not commence work on the assumption that B.I.G. has verified permits, insurance, tax obligations or legal terms. "
         "Resolve missing obligations and obtain appropriate professional review before signing."},
        {"heading": "Provider signature — blank, not captured",
         "body": f"Authorized name: {f['representative_name']}\nSignature: __________________________   Date: ______________"},
        {"heading": "Client signature — blank, not captured",
         "body": f"Name: {f['client_name']}\nSignature: __________________________   Date: ______________"},
        {"heading": "Preparation reference", "body": f"Business Project: {source['project_name']}. "
         f"Selected plan: {source['plan_name']}. Template {TEMPLATE_KEY} v{source['template_version']}. "
         "No signature, government filing, funding application or external transmission has occurred."},
    ]


def render(source):
    if source["template_version"] != TEMPLATE_VERSION:
        raise ValueError("Unsupported document renderer version")
    body = "".join(f"<section><h2>{html.escape(s['heading'])}</h2><p>{html.escape(s['body'])}</p></section>"
                   for s in sections(source))
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Cleaning Service Agreement — unsigned</title>'
            '<style>body{font:16px/1.6 Georgia,serif;max-width:850px;margin:36px auto;padding:20px;color:#172a2d}'
            'h1{font-size:28px}h2{font-size:19px;margin-top:25px}p{white-space:pre-wrap;overflow-wrap:anywhere}'
            '@media print{body{margin:0;max-width:none}section{break-inside:avoid}}</style>'
            '<h1>Cleaning Service Agreement</h1><p><strong>Prepared for review — unsigned</strong></p>'
            + body + '</html>').encode("utf-8")


def digest(source):
    return hashlib.sha256(render(source)).hexdigest()


def canonical(source):
    return json.dumps(source, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
