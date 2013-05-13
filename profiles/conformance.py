profiles = {
    'l2' : {
        'mandatory' : 'Grp50No10,Grp50No20,Grp50No30,Grp50No40,Grp50No50,Grp50No60,Grp50No140,Grp50No190',
        'matches' : 'dl_dst,dl_src,dl_type,dl_vlan,dl_vlan_pcp'
        },
    'l3' : {
        'mandatory' : 'Grp50No10,Grp50No20,Grp50No50,Grp50No80,Grp50No90,Grp50No150,Grp50No180,Grp50No190',
        'matches' : 'nw_src,nw_dst'
        },
    'full' : {
        'mandatory' : 'Grp50No10,Grp50No20,Grp50No30,Grp50No40,Grp50No50,Grp50No60,Grp50No80,Grp50No90,Grp50No140,Grp50No150,Grp50No180,Grp50No190',
        'matches' : 'dl_dst,dl_src,dl_type,dl_vlan,dl_vlan_pcp,nw_src,nw_dst'
        },
    # Add custom match profiles below
}
