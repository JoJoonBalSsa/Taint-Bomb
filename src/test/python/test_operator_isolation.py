import unittest

import test_operator_regressions as regressions


class OperatorIsolationTests(unittest.TestCase):
    def setUp(self):
        self.harness = regressions.OperatorRegressionTests(
            "test_integral_arithmetic_and_relational_categories_are_obfuscated"
        )

    def test_inferred_lambda_shadow_does_not_borrow_outer_integral_type(self):
        method = """static boolean probe(int a) {
    class Inner {
        boolean run() {
            java.util.function.DoublePredicate predicate = a -> {
                if (a > 0) return true;
                return false;
            };
            return predicate.test(Double.NaN);
        }
    }
    return new Inner().run();
}"""
        transformed = self.harness._transform_and_compare(
            method,
            "System.out.print(probe(1));",
        )
        self.assertEqual(method, transformed)

    def test_supported_integral_condition_still_rewrites(self):
        method = (
            "static boolean probe(int value) { "
            "if (value > 0) return true; return false; }"
        )
        transformed = self.harness._transform_and_compare(
            method,
            "System.out.print(probe(-1)+\":\"+probe(1));",
        )
        self.assertNotEqual(method, transformed)
        self.assertNotIn("value > 0", transformed)


if __name__ == "__main__":
    unittest.main()
