from app.tests.mixins import JsonRpcTestMixin, BaseTestCase


class FeedAPITestCase(JsonRpcTestMixin, BaseTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def setUp(self) -> None:
        pass
