import os
import pytest
import requests
import logging

from zapv2 import ZAPv2
from requests.exceptions import ConnectionError

from scbzapv2.zap_configuration import ZapConfiguration
from scbzapv2.zap_context import ZapConfigureContext
from scbzapv2.zap_spider import ZapConfigureSpider
from scbzapv2.zap_scanner import ZapConfigureActiveScanner

def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "tests", "docker-compose.yaml")

@pytest.fixture(scope="session")
def get_bodgeit_url(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("bodgeit", 8080)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return url

@pytest.fixture(scope="session")
def get_juiceshop_url(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("juiceshop", 3000)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return url

@pytest.fixture(scope="session")
def get_zap_url(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("zap", 8090)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return url

@pytest.fixture(scope="session")
def get_zap_instance(docker_ip, docker_services, get_zap_url) -> ZAPv2: 
    
    # MANDATORY. Define the API key generated by ZAP and used to verify actions.
    apiKey = 'eor898q1luuq8054e0e5r9s3jh'

    # MANDATORY. Define the listening address of ZAP instance
    localProxy = {
        "http": get_zap_url,
        "https": get_zap_url.replace("http", "https")
    }

    logging.info('Configuring ZAP Instance with %s', localProxy)
    # Connect ZAP API client to the listening address of ZAP instance
    zap = ZAPv2(proxies=localProxy, apikey=apiKey)

    return zap

def test_all_services_available(get_bodgeit_url, get_juiceshop_url, get_zap_url):
    response = requests.get(get_bodgeit_url + "/bodgeit/")
    assert response.status_code == 200
    
    response = requests.get(get_juiceshop_url + "/#/")
    assert response.status_code == 200

    response = requests.get(get_zap_url + "/UI/core/")
    assert response.status_code == 200

def test_bodgeit_scan(get_bodgeit_url, get_juiceshop_url, get_zap_instance: ZAPv2):

    zap = get_zap_instance
    test_config_yaml = "./tests/mocks/scan-full-bodgeit-docker/"
    
    config = ZapConfiguration(test_config_yaml)
    target = "http://bodgeit:8080/"

    logging.info('Configuring ZAP Context')
    # Starting to configure the ZAP Instance based on the given Configuration
    if config.has_configurations() and config.has_context_configurations:
        local_zap_context = ZapConfigureContext(zap, config)

        configured_context = zap.context.context("scb-bodgeit-context")
        assert configured_context["name"] == "scb-bodgeit-context"

    logging.info('Starting ZAP Spider with target %s', target)
    # if a ZAP Configuration is defined start to configure the running ZAP instance (`zap`)
    if config and config.has_spider_configurations:
        # Starting to configure the ZAP Spider Instance based on the given Configuration
        zap_spider = ZapConfigureSpider(zap, config)
        spider_id = zap_spider.start_spider_by_url(target, False)

        assert int(zap.spider.status(spider_id)) > 0

        zap_spider.wait_until_http_spider_finished(spider_id)
        result_urls = len(zap.core.urls())

        assert int(result_urls) > 10

    logging.info('Starting ZAP Scanner with target %s', target)
    # if a ZAP Configuration is defined start to configure the running ZAP instance (`zap`)
    if config and config.has_scan_configurations:
        # Starting to configure the ZAP Instance based on the given Configuration
        zap_scan = ZapConfigureActiveScanner(zap, config)
        # Search for the corresponding context based on the given targetUrl which should correspond to defined the spider url
        scan_id = zap_scan.start_scan_by_url(target)

        assert int(zap.ascan.status(scan_id)) > 0

        zap_scan.wait_until_finished(scan_id)
        result_urls = len(zap.core.urls())

        assert int(result_urls) > 10

        alerts = zap_scan.get_alerts(target, [], [])

        logging.info('Found ZAP Alerts: %s', str(len(alerts)))

        assert int(len(alerts)) >= 5
    
def test_juiceshop_scan(get_bodgeit_url, get_juiceshop_url, get_zap_instance: ZAPv2):
    
    zap = get_zap_instance
    test_config_yaml = "./tests/mocks/scan-full-juiceshop-docker/"
    
    config = ZapConfiguration(test_config_yaml)
    target = "http://juiceshop:3000/"

    logging.info('Configuring ZAP Context')
    # Starting to configure the ZAP Instance based on the given Configuration
    if config.has_configurations() and config.has_context_configurations:
        local_zap_context = ZapConfigureContext(zap, config)

        configured_context = zap.context.context("scb-juiceshop-context")
        assert configured_context["name"] == "scb-juiceshop-context"

    logging.info('Starting ZAP Spider with target %s', target)
    # if a ZAP Configuration is defined start to configure the running ZAP instance (`zap`)
    if config and config.has_spider_configurations:
        # Starting to configure the ZAP Spider Instance based on the given Configuration
        zap_spider = ZapConfigureSpider(zap, config)
        spider_id = zap_spider.start_spider_by_url(target, True)

        assert zap.ajaxSpider.status == 'running'

        zap_spider.wait_until_ajax_spider_finished()
        result_urls = len(zap.core.urls())

        assert int(result_urls) > 10

    logging.info('Starting ZAP Scanner with target %s', target)
    # if a ZAP Configuration is defined start to configure the running ZAP instance (`zap`)
    if config and config.has_scan_configurations:
        # Starting to configure the ZAP Instance based on the given Configuration
        zap_scan = ZapConfigureActiveScanner(zap, config)
        # Search for the corresponding context based on the given targetUrl which should correspond to defined the spider url
        scan_id = zap_scan.start_scan_by_url(target)

        assert int(zap.ascan.status(scan_id)) > 0

        zap_scan.wait_until_finished(scan_id)
        result_urls = len(zap.core.urls())

        assert int(result_urls) > 10

        alerts = zap_scan.get_alerts(target, [], [])

        logging.info('Found ZAP Alerts: %s', str(len(alerts)))

        assert int(len(alerts)) >= 3

# # https://medium.com/opsops/deepdive-into-pytest-parametrization-cb21665c05b9
# @pytest.mark.parametrize("config_folder", ["./tests/mocks/scan-full-bodgeit/", "./tests/mocks/scan-full-juiceshop/"])
# def test_scan_matrix(get_bodgeit_url, get_juiceshop_url, config_folder: str, get_zap_instance: ZAPv2):
    
#     zap = get_zap_instance
#     test_config_yaml = config_folder    
    
#     config = ZapConfiguration(test_config_yaml)
#     target = "http://juiceshop:3000/"

#     logging.info('Configuring ZAP Context')
#     # Starting to configure the ZAP Instance based on the given Configuration
#     if config.has_configurations() and config.has_context_configurations:
#         local_zap_context = ZapConfigureContext(zap, config)

#         configured_context = zap.context.context("scb-juiceshop-context")
#         assert configured_context["name"] == "scb-juiceshop-context"

#     logging.info('Starting ZAP Spider with target %s', target)
#     # if a ZAP Configuration is defined start to configure the running ZAP instance (`zap`)
#     if config and config.has_spider_configurations:
#         # Starting to configure the ZAP Spider Instance based on the given Configuration
#         zap_spider = ZapConfigureSpider(zap, config)
#         spider_id = zap_spider.start_spider_by_url(target, True)

#         assert zap.ajaxSpider.status == 'running'

#         zap_spider.wait_until_ajax_spider_finished()
#         result_urls = len(zap.core.urls())

#         assert int(result_urls) > 10

#     logging.info('Starting ZAP Scanner with target %s', target)
#     # if a ZAP Configuration is defined start to configure the running ZAP instance (`zap`)
#     if config and config.has_scan_configurations:
#         # Starting to configure the ZAP Instance based on the given Configuration
#         zap_scan = ZapConfigureActiveScanner(zap, config)
#         # Search for the corresponding context based on the given targetUrl which should correspond to defined the spider url
#         scan_id = zap_scan.start_scan_by_url(target)

#         assert int(zap.ascan.status(scan_id)) >= 0

#         zap_scan.wait_until_finished(scan_id)
#         result_urls = len(zap.core.urls())

#         assert int(result_urls) > 10

#         alerts = zap_scan.get_alerts(target, [], [])

#         logging.info('Found ZAP Alerts: %s', str(len(alerts)))

#         assert int(len(alerts)) >= 3

