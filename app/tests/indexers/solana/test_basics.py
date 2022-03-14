import unittest

import aiohttp
from aiohttp import ClientTimeout

from app.indexers.solana.sme_indexer import get_nft_data


class BasicFunctionsTestCase(unittest.IsolatedAsyncioTestCase):
    wrong_mime_type_uri = 'https://cdn.piggygang.com/meta/3a1b4e3d63dc04a467af7d5cc25b730b.json'
    wrong_mime_type_expected = {'name': '#2264', 'symbol': 'PSG', 'external_url': 'https://piggygang.com',
                                'description': '10,000 cute & cruel piggies living on the Solana lands. Each of them are randomly generated with more than 90+ hand drawn traits!',
                                'seller_fee_basis_points': 500, 'collection': 'Piggy Sol Gang',
                                'image': 'https://cdn.piggygang.com/imgs/3a1b4e3d63dc04a467af7d5cc25b730b.jpg',
                                'attributes': [{'trait_type': 'Name', 'value': '#2264'},
                                               {'trait_type': 'Background', 'value': 'Yellow'},
                                               {'trait_type': 'Body', 'value': 'Yellow'},
                                               {'trait_type': 'Clothes', 'value': 'Singlet'},
                                               {'trait_type': 'Earring', 'value': 'Gold Ring'},
                                               {'trait_type': 'Eyes', 'value': 'Laser'},
                                               {'trait_type': 'Head', 'value': 'Cowboy Hat'},
                                               {'trait_type': 'Mouth', 'value': 'Neutral'}],
                                'properties': {'category': 'image', 'files': [
                                    {'uri': 'https://cdn.piggygang.com/imgs/3a1b4e3d63dc04a467af7d5cc25b730b.jpg',
                                     'type': 'image/jpeg'}], 'creators': [
                                    {'address': 'Pigv3gFWLWJL8QwrFBkdZLe1RYzNJTSJPGEUNVimJjh', 'share': 100}]}}

    redirected_url_uri = 'https://www.arweave.net/wt21uiUhlgyg3aVXamH7usDYGy1tdAvzT1ySG5P0GJM?ext=json'
    redirected_url_expected = {"name": "#063", "symbol": "NFTPro", "description": "", "seller_fee_basis_points": 1000,
                               "image": "https://www.arweave.net/OTePM1dP8ggG_PK9yovc1VrWiVHGkJeEIDHYN44EF04?ext=PNG",
                               "attributes": [{"trait_type": "Background", "value": "Numb"},
                                              {"trait_type": "Ghost", "value": "Black in death before dishonor hoodie"},
                                              {"trait_type": "Pants", "value": "3 stripes black pants"},
                                              {"trait_type": "BMX", "value": "XXX"},
                                              {"trait_type": "Shoes", "value": "Air Force 1 Low '07 Virgil x MoMA"},
                                              {"trait_type": "Hat", "value": "Black blue dreadlocks"},
                                              {"trait_type": "Accessories", "value": "XXX tattoos"}],
                               "external_url": "", "properties": {"files": [
            {"uri": "https://www.arweave.net/-N6fG7_AKkhIU8ZZHYxy5L_Mqe5pvoSqVTpBgQDnrZE?ext=PNG",
             "type": "image/png"}], "category": "image", "creators": [
            {"address": "DRyaqzqqQAq7no4GUNesVRtDWWkSF1M963CmegzFhrWF", "verified": True, "share": 100}]}}

    async def test_get_json_from_wrong_mime_types(self):
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=15.0), requote_redirect_url=False) as client:
            _, nft_raw_data = await get_nft_data(client, 0, self.wrong_mime_type_uri)
            self.assertDictEqual(self.wrong_mime_type_expected, nft_raw_data)

    async def test_redirect_urls(self):
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=15.0), requote_redirect_url=False) as client:
            _, nft_raw_data = await get_nft_data(client, 0, self.redirected_url_uri)
            self.assertDictEqual(self.redirected_url_expected, nft_raw_data)
