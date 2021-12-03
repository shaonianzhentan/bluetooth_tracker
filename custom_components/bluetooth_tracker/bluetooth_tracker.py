import sys, asyncio, logging, re, datetime
from contextlib import suppress
from homeassistant.helpers.event import async_track_time_interval
from .const import PING_TIMEOUT

_LOGGER = logging.getLogger(__name__)
PING_MATCHER = re.compile(
    r"(?P<min>\d+.\d+)\/(?P<avg>\d+.\d+)\/(?P<max>\d+.\d+)\/(?P<mdev>\d+.\d+)"
)

PING_MATCHER_BUSYBOX = re.compile(
    r"(?P<min>\d+.\d+)\/(?P<avg>\d+.\d+)\/(?P<max>\d+.\d+)"
)

WIN32_PING_MATCHER = re.compile(r"(?P<min>\d+)ms.+(?P<max>\d+)ms.+(?P<avg>\d+)ms")
TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=12)

class BluetoothTracker():

    def __init__(self, hass, host, mac, entity_id) -> None:
        self.hass = hass
        self._ip_address = host
        self.mac = mac
        self.entity_id = entity_id
        self._count = 3
        # 错误计数
        self.error_count = 0
        self.data = {}
        self.is_alive = False
        if sys.platform == "win32":
            self._ping_cmd = [
                "ping",
                "-n",
                str(self._count),
                "-w",
                "1000",
                self._ip_address,
            ]
        else:
            self._ping_cmd = [
                "ping",
                "-n",
                "-q",
                "-c",
                str(self._count),
                "-W1",
                self._ip_address,
            ]
        self.remove_listener = async_track_time_interval(hass, self.async_update, TIME_BETWEEN_UPDATES)

    async def async_ping(self):
        """Send ICMP echo request and return details if success."""
        pinger = await asyncio.create_subprocess_exec(
            *self._ping_cmd,
            stdin=None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out_data, out_error = await asyncio.wait_for(
                pinger.communicate(), self._count + PING_TIMEOUT
            )

            if out_data:
                _LOGGER.debug(
                    "Output of command: `%s`, return code: %s:\n%s",
                    " ".join(self._ping_cmd),
                    pinger.returncode,
                    out_data,
                )
            if out_error:
                _LOGGER.debug(
                    "Error of command: `%s`, return code: %s:\n%s",
                    " ".join(self._ping_cmd),
                    pinger.returncode,
                    out_error,
                )

            if pinger.returncode > 1:
                # returncode of 1 means the host is unreachable
                _LOGGER.exception(
                    "Error running command: `%s`, return code: %s",
                    " ".join(self._ping_cmd),
                    pinger.returncode,
                )

            if sys.platform == "win32":
                match = WIN32_PING_MATCHER.search(
                    str(out_data).rsplit("\n", maxsplit=1)[-1]
                )
                rtt_min, rtt_avg, rtt_max = match.groups()
                return {"min": rtt_min, "avg": rtt_avg, "max": rtt_max, "mdev": ""}
            if "max/" not in str(out_data):
                match = PING_MATCHER_BUSYBOX.search(
                    str(out_data).rsplit("\n", maxsplit=1)[-1]
                )
                rtt_min, rtt_avg, rtt_max = match.groups()
                return {"min": rtt_min, "avg": rtt_avg, "max": rtt_max, "mdev": ""}
            match = PING_MATCHER.search(str(out_data).rsplit("\n", maxsplit=1)[-1])
            rtt_min, rtt_avg, rtt_max, rtt_mdev = match.groups()
            return {"min": rtt_min, "avg": rtt_avg, "max": rtt_max, "mdev": rtt_mdev}
        except asyncio.TimeoutError:
            _LOGGER.exception(
                "Timed out running command: `%s`, after: %ss",
                self._ping_cmd,
                self._count + PING_TIMEOUT,
            )
            if pinger:
                with suppress(TypeError):
                    await pinger.kill()
                del pinger

            return False
        except AttributeError:
            return False

    async def async_update(self, now) -> None:
        # print(now)
        self.data = await self.async_ping()
        self.is_alive = bool(self.data)
        hass = self.hass
        entity_id = self.entity_id
        if self.is_alive:
            self.error_count = 0
            state = hass.states.get(entity_id)
            if state is not None and state.state != 'home':
                hass.states.async_set(entity_id, 'home', attributes=state.attributes)
        else:
            # 错误5次，则设置为不在家
            self.error_count = self.error_count + 1
            if self.error_count > 5:
                self.error_count = 0
                # 设置为不在家
                state = hass.states.get(entity_id)
                if state is not None and state.state != 'not_home':
                    hass.states.async_set(entity_id, 'not_home', attributes=state.attributes)

