import unittest
from database.database import Database
from datastructures.dialogueact import DialogueAct
from datastructures.dialoguestate import DialogueState

class TestStateUpdate(unittest.TestCase):
    def setUp(self):
        self.db = Database()

    def test_update(self):
        results = self.db.find_restaurants_single_option({"area":"centre", "pricerange":"cheap"})
        self.assertEqual(len(results), 15)