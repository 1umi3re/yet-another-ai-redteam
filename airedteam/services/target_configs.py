from __future__ import annotations
from sqlalchemy import select
from airedteam.storage.models import TargetConfig
from airedteam.storage.secretbox import SecretBox


class TargetConfigService:
    def __init__(self, session_factory, secret_box: SecretBox) -> None:
        self._sf = session_factory
        self._box = secret_box

    async def create(self, *, name: str, plugin: str, params: dict, secret: dict | None = None) -> TargetConfig:
        async with self._sf() as s:
            ct = self._box.encrypt(secret) if secret else None
            row = TargetConfig(name=name, plugin=plugin, params_json=params, secret_ciphertext=ct)
            s.add(row); await s.commit(); await s.refresh(row); return row

    async def list(self) -> list[TargetConfig]:
        async with self._sf() as s:
            r = await s.execute(select(TargetConfig).order_by(TargetConfig.created_at.desc()))
            return list(r.scalars().all())

    async def get(self, cfg_id: str) -> TargetConfig | None:
        async with self._sf() as s:
            return await s.get(TargetConfig, cfg_id)

    async def delete(self, cfg_id: str) -> None:
        async with self._sf() as s:
            row = await s.get(TargetConfig, cfg_id)
            if row:
                await s.delete(row); await s.commit()

    async def resolve_for_runtime(self, cfg_id: str) -> dict:
        cfg = await self.get(cfg_id)
        if cfg is None:
            raise KeyError(cfg_id)
        params = dict(cfg.params_json or {})
        if cfg.secret_ciphertext:
            params.update(self._box.decrypt(cfg.secret_ciphertext))
        return {"plugin": cfg.plugin, "params": params}
