import sqlite3, json


class Database(object):

    dbfile = "resources/CamRestaurants-dbase.db"
    ontologyFile = "resources/CamRestaurants-rules.json"
    ontology = None
    db_connection = None
    cursor = None

    def __init__(self):
        try:
            self.db_connection = sqlite3.connect(self.dbfile)
            self.db_connection.row_factory = (
                self._dict_factory
            )  # for getting entities back as python dict's
            self.cursor = self.db_connection.cursor()
        except Exception as e:
            print(e)
            print("Could not load database file: {}}".format(self.dbfile))
            exit(1)

        try:
            with open(self.ontologyFile) as ontofile:
                self.ontology = json.load(ontofile)
        except IOError:
            print("No such file or directory: " + self.ontologyFile)
            exit()
        return

    def find_restaurants_multiple_option(
        self, constraints: dict, negated_values: set[str]
    ) -> tuple[dict, dict]:
        for area in constraints["area"]:
            for pricerange in constraints["pricerange"]:
                for food in constraints["food"]:
                    result = self.find_restaurants_single_option(
                        {"area": area, "pricerange": pricerange, "food": food}
                    )
                    result = [r for r in result if r["name"] not in negated_values]
                    if result:
                        return result, {
                            "area": area,
                            "pricerange": pricerange,
                            "food": food,
                        }
        return [], {}

    def find_restaurants_single_option(self, constraints: dict) -> dict:
        query = "select * from CamRestaurants where "

        consts = []

        for slot in self.ontology["slots"]:
            if slot in constraints:
                consts.append(
                    '{} = "{}" COLLATE NOCASE'.format(slot, constraints[slot])
                )

        if len(consts):
            query += " and ".join(consts)
        else:
            query += "1"

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        return results

    def find_restaurant_by_name(self, name_list: list[str]) -> tuple[list, dict]:
        for name in name_list:
            results = self.find_restaurants_single_option({"name": name})
            if results:
                first_result = results[0]
                # params zum update das dialogue zustands.
                found_params = {
                    "name": first_result.get("name", ""),
                    "area": first_result.get("area", ""),
                    "pricerange": first_result.get("pricerange", ""),
                    "food": first_result.get("food", ""),
                    "signature": first_result.get("signature", ""),
                    "phone": first_result.get("phone", ""),
                    "description": first_result.get("description", ""),
                }
                return results, found_params
            return [], {}

    def get_all_attribute_values(self, attribute: str) -> set:
        """Get all unique values for a given attribute from the database."""
        query = f"SELECT DISTINCT {attribute} FROM CamRestaurants"
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        attribute_values = set()
        for row in results:
            if row[attribute] is not None:
                attribute_values.add(row[attribute])
        return attribute_values

    def _dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
