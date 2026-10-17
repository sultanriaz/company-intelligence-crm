from typing import Any, Dict, Tuple
from jinja2 import Environment, BaseLoader

jinja_env = Environment(loader=BaseLoader(), autoescape=True)


def render_email_template(
    subject_template: str,
    body_template: str,
    context: Dict[str, Any],
    unsubscribe_url: str = "https://company-intelligence.local/unsubscribe",
    company_address: str = "100 Market St, Suite 400, San Francisco, CA 94105",
) -> Tuple[str, str, str]:
    """
    Renders subject and body templates with given context variables.
    Appends required compliance footer (CAN-SPAM/GDPR) to plain text and HTML.
    Returns: (rendered_subject, rendered_body_text, rendered_body_html)
    """
    full_context = dict(context)
    full_context["unsubscribe_url"] = unsubscribe_url
    full_context["company_address"] = company_address

    subj_tmpl = jinja_env.from_string(subject_template)
    body_tmpl = jinja_env.from_string(body_template)

    rendered_subject = subj_tmpl.render(**full_context).strip()
    raw_body = body_tmpl.render(**full_context).strip()

    # Plain text version
    body_text = (
        f"{raw_body}\n\n"
        f"---\n"
        f"{company_address}\n"
        f"To unsubscribe from future communications: {unsubscribe_url}"
    )

    # HTML version
    body_html = (
        f"<div>{raw_body.replace(chr(10), '<br>')}</div>"
        f"<hr style='margin-top:24px;border:none;border-top:1px solid #e2e8f0;' />"
        f"<p style='font-size:12px;color:#64748b;'>"
        f"{company_address}<br>"
        f"<a href='{unsubscribe_url}' style='color:#6366f1;'>Unsubscribe</a>"
        f"</p>"
    )

    return rendered_subject, body_text, body_html
