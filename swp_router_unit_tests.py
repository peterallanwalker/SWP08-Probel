import time
import random

import cli_utils
import connectIO_cli_settings as config
from swp_router_06 import Router

TITLE = "Unit tests for swp_router.py"
VERSION = 0.6


def test_connect(router):
    rand_src = router.sources[random.randint(0, len(router.sources) - 1)]
    rand_dst = router.destinations[random.randint(0, len(router.destinations) - 1)]
    #print(40 * "-" + "\n[swp_router.test_connect]")
    #print("  Random source:\n", rand_src)
    #print("\n  Random Destination:\n", rand_dst)
    router.connect(rand_src, rand_dst)
    time.sleep(1)
    router.process_incoming_messages()

    if not rand_dst.connected_source:
        print("\n[swp_router_tests.test_connect]: FAIL")

    if rand_dst.connected_source == rand_src:
        print("\n[swp_router_tests.test_connect]: PASS")
        #print("\n", rand_dst)
    else:
        print("\n[swp_router_tests.test_connect]: FAIL")


def test_update_source_label(router):
    rand_src = router.sources[random.randint(0, len(router.sources) - 1)]
    router.update_source_label(rand_src, "test label")
    time.sleep(1)
    router.process_incoming_messages()
    if rand_src.connected_source == "test label":
        print("[swp_router_unit_tests.test_update_source_label]: PASS")
    else:
        print("[swp_router_unit_tests.test_update_source_label]: FAIL")


if __name__ == '__main__':
    cli_utils.print_header(TITLE, VERSION)

    settings = config.get_settings()  # - present last used settings and prompt for confirm/edit
    config.save_settings(settings)  # - Save user confirmed settings for next startup

    io_config = 'VirtualPatchbaysb.csv'
    router = Router(settings, io_config=io_config)

    # - Wait for connection
    while router.connection.status != 'Connected':
        pass

    test_connect(router)
    test_update_source_label(router)
