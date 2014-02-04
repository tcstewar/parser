from ca.nengo.model.impl import NetworkImpl, EnsembleOrigin, EnsembleTermination
from ca.nengo.model.nef.impl import DecodedTermination, DecodedOrigin, NEFEnsembleImpl
from nef import *
from ca.nengo.model.impl import NetworkArrayImpl

def analyze_projections(net, proj_map, node_dict):
    for projection in net.projections:
        term = projection.termination
        if( isinstance(term, NetworkImpl.TerminationWrapper) ):
            base_term = term.getBaseTermination()
        else:
            base_term = term
        orig = projection.origin
        if( isinstance(orig, NetworkImpl.OriginWrapper) ):
            base_orig = orig.getBaseOrigin()
        else:
            base_orig = orig

        if( base_orig.node in node_dict.keys() and base_term.node in node_dict.keys() ):
            if( hasattr(base_orig, "getNodeOrigins") and isinstance(base_orig.getNodeOrigins()[0], DecodedOrigin) ):
                origs = base_orig.getNodeOrigins()
            else:
                origs = [base_orig]

            for origin in origs:
                if( hasattr(base_term, "getNodeTerminations") and isinstance(base_term.getNodeTerminations()[0], DecodedTermination) ):
                    for ens_term in base_term.getNodeTerminations():
                        proj_map.append(net.name + "," + orig.name + "," + node_dict[origin.node]["path"] + "," + term.name + "," + node_dict[ens_term.node]["path"] +"\n")
                        add_proj_node_dict(node_dict, origin.node, ens_term.node)
                else:
                    proj_map.append(net.name + "," + orig.name + "," + node_dict[origin.node]["path"] + "," + term.name + "," + node_dict[base_term.node]["path"] +"\n")
                    add_proj_node_dict(node_dict, origin.node, base_term.node)
        if( not base_orig.node in node_dict.keys() ):
            print "Warning: In %s, node %s not found for projection %s:%s(%s) -> %s:%s(%s)" % (net.name, base_orig.node.name, base_orig.node.name, base_orig.name, orig.name, base_term.node.name, base_term.name, term.name)
        if( not base_term.node in node_dict.keys() ):
            print "Warning: In %s, node %s not found for projection %s:%s(%s) -> %s:%s(%s)" % (net.name, base_term.node.name, base_orig.node.name, base_orig.name, orig.name, base_term.node.name, base_term.name, term.name)
        
    for node in net.nodes:
        if( isinstance(node, NetworkImpl) ):
            analyze_projections(node, proj_map, node_dict)


def add_proj_node_dict(node_dict, orig_node, term_node):
#    node_dict[orig_node]["fan_out"].append(term_node)
    node_dict[orig_node]["fan_out"].append(node_dict[term_node]["path"])
    node_dict[orig_node]["fan_out_nsize"] = node_dict[orig_node]["fan_out_nsize"] + node_dict[term_node]["size"]
#    node_dict[term_node]["fan_in"].append(orig_node)
    node_dict[term_node]["fan_in"].append(node_dict[orig_node]["path"])
    node_dict[term_node]["fan_in_nsize"] = node_dict[term_node]["fan_in_nsize"] + node_dict[orig_node]["size"]


def init_node_dict(net, node_dict, curr_path):
    for node in net.nodes:
        node_info = {}
        node_info["name"] = node.name
        node_info["path"] = curr_path + node.name
        if( hasattr(node, "getNeuronCount") ):
            node_info["size"] = node.getNeuronCount()
        else:
            node_info["size"] = 0
        node_info["fan_in"] = []
        node_info["fan_in_nsize"] = 0
        node_info["fan_out"] = []
        node_info["fan_out_nsize"] = 0
        node_dict[node] = node_info
        if( isinstance(node, NetworkImpl) ):
            init_node_dict(node, node_dict, curr_path + node.name + ".")


def write_proj_map(filename, proj_map):
    write_file = open(filename, "w")
    write_file.write("Node,Origin,OriginNode,Termination,TerminationNode\n")
    for proj in proj_map:
        write_file.write(proj)
    write_file.close()


def write_node_info(filename, node_dict):
    write_file = open("node.csv", "w")
    write_file.write("Node,Size,FanIn,FanInObj,FanInSize,FanOut,FanOutObj,FanOutSize\n")

    node_dict_keys = node_dict.keys()
    node_dict_keys = sorted(node_dict_keys, key = lambda x: node_dict[x]["path"])

    for key in node_dict_keys:
        info = node_dict[key]
        if( isinstance(key, NEFEnsembleImpl) ):
            write_file.write("%s,%i,%i,%s,%i,%i,%s,%i\n" % (info["path"], info["size"], len(info["fan_in"]), str(info["fan_in"]).replace(",",";",), \
            info["fan_in_nsize"], len(info["fan_out"]), str(info["fan_out"]).replace(",",";",), info["fan_out_nsize"]))
    write_file.close()


def run_me(net):
    if( isinstance(net, Network) ):
        net = net.network

    node_dict = {}
    proj_map = []
    init_node_dict(net, node_dict, "")
    analyze_projections(net, proj_map, node_dict)
    
    write_proj_map("proj.csv", proj_map)
    write_node_info("node.csv", node_dict)
