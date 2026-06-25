import html
import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urlparse


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


@dataclass
class IndicatorReport:
    kind: str
    value: str
    summary: str
    details: list[str]
    recommendations: list[str]

    def to_html(self) -> str:
        details = "\n".join(f"• {item}" for item in self.details)
        recommendations = "\n".join(f"• {item}" for item in self.recommendations)
        safe_value = html.escape(self.value)
        return (
            f"🛡 <b>LIA SECURITY RADAR</b>\n\n"
            f"<b>Тип:</b> {self.kind}\n"
            f"<b>Объект:</b> <code>{safe_value}</code>\n"
            f"<b>Итог:</b> {self.summary}\n\n"
            f"<b>Факты:</b>\n{details}\n\n"
            f"<b>Что сделать:</b>\n{recommendations}\n\n"
            f"<i>Проверка пассивная: без взлома, атак и скрытого сбора данных.</i>"
        )


class SecurityTools:
    def detect_indicator(self, raw_value: str) -> tuple[str, str]:
        value = (raw_value or "").strip()
        if not value:
            return "empty", value

        parsed = urlparse(value if "://" in value else f"//{value}")
        host = parsed.hostname or value

        try:
            ipaddress.ip_address(value)
            return "ip", value
        except ValueError:
            pass

        if value.startswith(("http://", "https://")):
            return "url", value

        if EMAIL_RE.match(value):
            return "email", value
        if "." in host and " " not in host:
            return "domain", host.lower()
        if USERNAME_RE.match(value.lstrip("@")):
            return "username", value.lstrip("@")
        return "text", value

    def analyze(self, raw_value: str) -> IndicatorReport:
        kind, value = self.detect_indicator(raw_value)
        if kind == "url":
            return self._analyze_url(value)
        if kind == "domain":
            return self._analyze_domain(value)
        if kind == "ip":
            return self._analyze_ip(value)
        if kind == "email":
            return self._analyze_email(value)
        if kind == "username":
            return self._analyze_username(value)
        return IndicatorReport(
            kind="текст",
            value=value or "—",
            summary="Не распознала индикатор. Пришли URL, домен, IP, email или username.",
            details=["Поддерживаются пассивные проверки без обращения к приватным базам."],
            recommendations=["Пример: <code>/sec https://example.com/login</code>", "Пример: <code>/sec 8.8.8.8</code>"],
        )

    def _analyze_url(self, value: str) -> IndicatorReport:
        parsed = urlparse(value)
        host = parsed.hostname or ""
        details = [f"Схема: <code>{parsed.scheme or 'нет'}</code>", f"Хост: <code>{host or 'нет'}</code>"]
        recommendations = ["Не вводи пароли, если домен похож на подделку или использует короткую ссылку."]

        risk = []
        if parsed.scheme != "https":
            risk.append("нет HTTPS")
            recommendations.append("Открывай только HTTPS-версию сайта, если она доступна.")
        if "@" in value:
            risk.append("символ @ в URL")
            recommendations.append("URL с <code>@</code> часто маскирует настоящий хост после этого символа.")
        if len(value) > 140:
            risk.append("слишком длинная ссылка")
        if re.search(r"(?:xn--|%[0-9a-fA-F]{2})", value):
            risk.append("кодировка/IDN может маскировать символы")
        if host:
            details.extend(self._resolve_host_details(host))

        summary = "Есть признаки риска: " + ", ".join(risk) if risk else "Явных красных флагов по структуре URL не найдено."
        recommendations.append("Проверь отправителя ссылки и не скачивай файлы из неизвестного источника.")
        return IndicatorReport("URL", value, summary, details, recommendations)

    def _analyze_domain(self, value: str) -> IndicatorReport:
        details = self._resolve_host_details(value)
        labels = value.split(".")
        risk = []
        if len(labels) > 4:
            risk.append("много поддоменов")
        if any(len(label) > 30 for label in labels):
            risk.append("очень длинная часть домена")
        if value.startswith("xn--") or ".xn--" in value:
            risk.append("IDN/punycode")
        summary = "Есть признаки риска: " + ", ".join(risk) if risk else "Домен выглядит нормально по базовой структуре."
        return IndicatorReport(
            "домен",
            value,
            summary,
            details,
            ["Сверь домен с официальным сайтом вручную.", "Для платежей и входа используй закладки или официальный поиск."],
        )

    def _analyze_ip(self, value: str) -> IndicatorReport:
        ip = ipaddress.ip_address(value)
        details = [f"Версия IP: IPv{ip.version}"]
        if ip.is_private:
            details.append("Адрес приватной сети, не маршрутизируется напрямую из интернета.")
        if ip.is_loopback:
            details.append("Loopback-адрес локальной машины.")
        if ip.is_multicast:
            details.append("Multicast-адрес.")
        if ip.is_global:
            details.append("Публичный глобально маршрутизируемый адрес.")
        try:
            hostname = socket.gethostbyaddr(value)[0]
            details.append(f"Reverse DNS: <code>{hostname}</code>")
        except OSError:
            details.append("Reverse DNS не найден или недоступен.")
        return IndicatorReport(
            "IP",
            value,
            "Базовая классификация IP выполнена.",
            details,
            ["Не сканируй чужие IP без разрешения.", "Для инцидента сохрани время, логи и источник появления IP."],
        )

    def _analyze_email(self, value: str) -> IndicatorReport:
        local, domain = value.rsplit("@", 1)
        details = [f"Домен почты: <code>{domain}</code>", f"Длина локальной части: {len(local)}"]
        details.extend(self._resolve_host_details(domain))
        risk = []
        if "+" in local:
            details.append("Есть plus-alias — это нормально для многих почтовых сервисов.")
        if domain.startswith("xn--") or ".xn--" in domain:
            risk.append("IDN/punycode в домене")
        summary = "Есть признаки риска: " + ", ".join(risk) if risk else "Email выглядит корректно по формату."
        return IndicatorReport(
            "email",
            value,
            summary,
            details,
            ["Не отправляй коды/пароли на email без подтверждения личности адресата.", "Для фишинга проверь домен отправителя и заголовки письма."],
        )

    def _analyze_username(self, value: str) -> IndicatorReport:
        details = [f"Длина: {len(value)}", "Подходит для ручного OSINT-поиска по публичным профилям."]
        return IndicatorReport(
            "username",
            value,
            "Username распознан. Автоматический сбор приватных данных не выполняется.",
            details,
            ["Ищи только публичные профили и не обходи настройки приватности.", "Сравни аватар, дату регистрации, стиль сообщений и связанные ссылки."],
        )

    def _resolve_host_details(self, host: str) -> list[str]:
        details = []
        try:
            infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
            ips = sorted({info[4][0] for info in infos})[:6]
            if ips:
                details.append("DNS A/AAAA: " + ", ".join(f"<code>{ip}</code>" for ip in ips))
            else:
                details.append("DNS-записи A/AAAA не найдены.")
        except OSError:
            details.append("DNS-разрешение не удалось.")
        return details


security_tools = SecurityTools()