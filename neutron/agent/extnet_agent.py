
from oslo_config import cfg
from oslo_service import service

from neutron.agent.extnet import config as extnet_config
from neutron.agent.linux import external_process
from neutron.agent.common import config
from neutron.common import topics
from neutron import service as neutron_service


def main(manager='neutron.agent.extnet.agent.ExtNetAgent'):

    cfg.CONF.register_opts(external_process.OPTS)
    cfg.CONF.register_opts(extnet_config.OPTS)
    config.register_agent_state_opts_helper(cfg.CONF)
    config.setup_logging()
    server = neutron_service.Service.create(
        binary='neutron-extnet-agent',
        topic=topics.EXTNET_AGENT,
        report_interval=cfg.CONF.AGENT.report_interval,
        manager=manager)
    service.launch(cfg.CONF, server).wait()
