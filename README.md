# Magnum Destination Monitor Collector

Magnum destination monitor collector is designed for the inSITE Poller program python module. The destination monitor collector uses the Magnum GraphQL API to query for SDVN destinations and source routing assignment. A custom dashboard is included to display destinations in an "airport view" fashion.

This module uses the Magnum SDVN destination tagging feature to query for only destinations that match a tag value.

The destination collection module has teh below distinct abilities and features:

1. Collects destination namesets names.
2. Uses the Magnum OIDC authentication.
3. Resolves the source device to a supplied nameset.
4. High level "airport view" dashboard to show destination and source assignment.

## Minimum Requirements:

-   inSITE Version 11 and service pack 2.
-   Magnum SDVN System supporting keycloak and GraphQL API
-   Python3.7 (_already installed on inSITE machine_)
-   Python3.7 Requests library (_already installed on inSITE machine_)

## Installation:

Installation of the module requires copying the script module into the poller modules folder:

1. Copy **destination_monitor.py** script to the poller python modules folder:

    ```
     cp scripts/destination_monitor.py /opt/evertz/insite/parasite/applications/pll-1/data/python/modules/
    ```

2. Restart the poller application

## Configuration:

To configure a poller to use the module start a new python poller configuration outlined below

1. Click the create a custom poller from the poller application settings page
2. Enter a Name, Summary and Description information
3. Enter the Magnum Server IP in the _Hosts_ tab
4. From the _Input_ tab change the _Type_ to **Python**
5. From the _Input_ tab change the _Metric Set Name_ field to **magnum**
6. From the _Input_ tab change the _Freqency_ value to **300000** (_5 minutes_)
7. Select the _Script_ tab, then paste the contents of **scripts/poller_config.py** into the script panel.

8. Update the below argument with the correct Magnum SDVN Cluster IP address and inSITE Nature name.

    - Update the _params_ argument with the client_id and secret information with the Magnum keycloak information.
    - Configure a tag to match destinations in the "tags" field.
    - Change the nameset to a different name if one is needed.

```
        params = {
            "magnum": hosts[-1],
            "client_id": "insite-poller",
            "secret": "secret",
            "tags": ["-ENC-NOC"],
            "nameset": "Global",
        }
```

10. Save changes, then restart the poller program.

## Testing:

The destination_monitor script can be ran manually from the shell using the following command with arguments

```
python destination_monitor.py [-h] -host <ip> [-client <client-id>] -secret <secret> [-name <nameset>] -t ENC-NOC TOC-NOC [ENC-NOC TOC-NOC ...]
```

Displaying the help command output

```
python .\destination_monitor.py -h
```

```
usage: destination_monitor.py [-h] -host <ip> [-client <client-id>] -secret <secret> [-name <nameset>] -t ENC-NOC TOC-NOC [ENC-NOC TOC-NOC ...]

Magnum Destination Poller

options:
  -h, --help            show this help message and exit
  -host <ip>, --magnum-host <ip>
                        Magnum IP Address
  -client <client-id>, --client-id <client-id>
                        Client ID in Magnum OIDC Credentials (default: 'insite-poller')
  -secret <secret>, --secret-key <secret>
                        Secret Key from the Magnum OIDC Credentials
  -name <nameset>, --nameset-name <nameset>
                        Nameset used to get the source label from (default: 'Global')
  -t ENC-NOC TOC-NOC [ENC-NOC TOC-NOC ...], --tags ENC-NOC TOC-NOC [ENC-NOC TOC-NOC ...]
                        Tags used to match destinations

```

Below are the summarization documents that are auto generated:

```
{
    "fields": {
        "s_dest_id": "a15a1cb5-d34c-5df0-98da-f3ebc05991ee",
        "s_dest_name": "XPT-ATL-NOC_RTR-VID-DST-46",
        "as_tags": [
            "ENC-ATL-NOC",
            "ENC",
            "ES-ROUTE",
            "ES-ENC-NOC"
        ],
        "s_src_name": "XPT-ATL-NOC_RTR-VID-SRC-1124",
        "s_src_id": "18bd5ba9-ee0f-5d71-8635-4881bd237d16",
        "s_src_name_resolved": "NGMC ITXE 12",
        "s_src_name_nameset": "Global",
        "s_long_name": "ATL LIVE 30 ENC SEC",
        "s_short_name": "ATL LIVE 30 ENC SEC",
        "s_global": "ATL-NOC-ATEME-DCT10-03-VID-DST-6"
    },
    "host": "1.1.1.1",
    "name": "dst_mon"
},
{
    "fields": {
        "s_dest_id": "fc291890-4fa4-52e7-a129-a84efa4812ff",
        "s_dest_name": "XPT-ATL-NOC_RTR-VID-DST-48",
        "as_tags": [
            "ENC-ATL-NOC",
            "ENC",
            "ES-ROUTE",
            "ES-ENC-NOC"
        ],
        "s_src_name": "",
        "s_src_id": "",
        "s_src_name_resolved": "",
        "s_src_name_nameset": "",
        "s_long_name": "ATL LIVE 32 ENC SEC",
        "s_short_name": "ATL LIVE 32 ENC SEC",
        "s_global": "ATL-NOC-ATEME-DCT10-03-VID-DST-8"
    },
    "host": "1.1.1.1",
    "name": "dst_mon"
}
```
