"""Config flow for yolink_local."""

import logging
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from yolink.local_hub_client import YoLinkLocalHubClient

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_HOST, CONF_NET_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Required(CONF_NET_ID): str,
    }
)


class InvalidAuth(Exception):
    """Error to indicate the hub rejected these credentials."""


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Confirm we can actually authenticate against this hub before saving."""
    session = aiohttp_client.async_get_clientsession(hass)
    client = YoLinkLocalHubClient(
        session,
        data[CONF_HOST],
        data[CONF_NET_ID],
        data[CONF_CLIENT_ID],
        data[CONF_CLIENT_SECRET],
    )
    if not await client.authenticate():
        raise InvalidAuth


class YoLinkLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for YoLink Local."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: collect hub IP, Client ID/Secret, Net ID."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NET_ID])
            self._abort_if_unique_id_configured()
            try:
                await _validate_input(self.hass, user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating YoLink Local Hub")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="YoLink Local", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )