from __future__ import annotations

from urllib.parse import parse_qsl, urlencode

from kiasumiles.hosted import app as hosted_app


class RestorePublicPath:
    """Restore the public path after Vercel's catch-all function rewrite."""

    def __init__(self, wrapped_app):
        self.wrapped_app = wrapped_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") not in {"http", "websocket"}:
            await self.wrapped_app(scope, receive, send)
            return

        query_items = parse_qsl(
            scope.get("query_string", b"").decode("utf-8"),
            keep_blank_values=True,
        )
        public_path = None
        forwarded_query = []
        for key, value in query_items:
            if key == "__kiasumiles_path" and public_path is None:
                public_path = value
            else:
                forwarded_query.append((key, value))

        if public_path is None:
            await self.wrapped_app(scope, receive, send)
            return

        restored_scope = dict(scope)
        restored_path = f"/{public_path.lstrip('/')}" if public_path else "/"
        restored_scope["path"] = restored_path
        restored_scope["raw_path"] = restored_path.encode("utf-8")
        restored_scope["query_string"] = urlencode(
            forwarded_query,
            doseq=True,
        ).encode("utf-8")
        await self.wrapped_app(restored_scope, receive, send)


app = RestorePublicPath(hosted_app)
