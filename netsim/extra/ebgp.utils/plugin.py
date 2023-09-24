from box import Box
from netsim.utils import log
from netsim import api

def pre_link_transform(topology: Box) -> None:
  # Error if BGP module is not loaded
  if 'bgp' not in topology.module:
    log.error(
      'BGP Module is not loaded.',
      log.IncorrectValue,
      'ebgp_utils')

'''
post_transform hook

As we're applying interface attributes to BGP sessions, we have to copy
interface BGP parameters supported by this plugin into BGP neighbor parameters
'''

def post_transform(topology: Box) -> None:
  config_name = api.get_config_name(globals())              # Get the plugin configuration name

  for n, ndata in topology.nodes.items():
    for intf in ndata.interfaces:
      if not isinstance(intf.get('bgp',None),Box):
        continue

      # Iterate over all link/interface attributes that have to be copied into neighbors
      for attr in ('as_override','allowas_in','default_originate','password'):
        attr_value = intf.bgp.get(attr,None)
        if not attr_value:                                  # Attribute not on the interface, move on
          continue
        
        # Iterate over all BGP neighbors trying to find neighbors on this interface
        for neigh in ndata.get('bgp', {}).get('neighbors', []):
          if neigh.ifindex == intf.ifindex and neigh.type == 'ebgp':
            neigh[attr] = attr_value                        # Found the neighbor, set neighbor attribute
            api.node_config(ndata,config_name)              # And remember that we have to do extra configuration

        if 'vrf' not in intf:                               # Not a VRF interface?
           continue                                         # ... great, move on

        # Now do the same 'copy interface attribute to neighbors' thing for VRF neighbors
        for neigh in ndata.vrfs[intf.vrf].get('bgp', {}).get('neighbors', []):
          if neigh.ifindex == intf.ifindex and neigh.type == 'ebgp':
            neigh[attr] = attr_value                        # Found the neighbor, set neighbor attribute
            api.node_config(ndata,config_name)              # And remember that we have to do extra configuration
