import pytest

from app.services.mtg_rotation_service import MtgRotationTarget, parse_mtg_rotation_targets


@pytest.mark.unit
def test_parse_mtg_rotation_targets_ok() -> None:
    raw = "wolf|root@100.120.178.115|/etc/mtg.toml|mtg;tw|root@100.97.163.69|/etc/mtg.toml|mtg"
    result = parse_mtg_rotation_targets(raw)

    assert result == [
        MtgRotationTarget(
            name="wolf",
            ssh_target="root@100.120.178.115",
            config_path="/etc/mtg.toml",
            service_name="mtg",
        ),
        MtgRotationTarget(
            name="tw",
            ssh_target="root@100.97.163.69",
            config_path="/etc/mtg.toml",
            service_name="mtg",
        ),
    ]


@pytest.mark.unit
def test_parse_mtg_rotation_targets_empty() -> None:
    assert parse_mtg_rotation_targets("") == []


@pytest.mark.unit
def test_parse_mtg_rotation_targets_bad_format() -> None:
    with pytest.raises(ValueError):
        parse_mtg_rotation_targets("wolf|root@host|/etc/mtg.toml")


@pytest.mark.unit
def test_parse_mtg_rotation_targets_unsafe_ssh() -> None:
    with pytest.raises(ValueError):
        parse_mtg_rotation_targets("wolf|root@host;rm -rf /|/etc/mtg.toml|mtg")
