import node from "eslint-plugin-n";
import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default [...compat.extends("eslint:recommended"), {
    plugins: {
        node,
    },

    languageOptions: {
        globals: {
            ...globals.node,
            Map: true,
            Promise: true,
        },

        ecmaVersion: 13,
        sourceType: "module",
    },

    rules: {
        "no-console": 0,
        "arrow-parens": ["error", "always"],
        "no-var": "error",
        "prefer-const": "error",
        "array-bracket-spacing": ["error", "never"],
        "comma-dangle": ["error", "never"],
        "computed-property-spacing": ["error", "never"],
        "eol-last": "error",
        eqeqeq: ["error", "smart"],

        indent: ["error", 4, {
            SwitchCase: 1,
        }],

        "no-confusing-arrow": ["error", {
            allowParens: false,
        }],

        "no-extend-native": "error",
        "no-mixed-spaces-and-tabs": "error",
        "func-call-spacing": ["error", "never"],
        "no-trailing-spaces": "error",
        "no-unused-vars": "error",
        "no-use-before-define": ["error", "nofunc"],
        "object-curly-spacing": ["error", "always"],
        "prefer-arrow-callback": "error",
        quotes: ["error", "single", "avoid-escape"],
        semi: ["error", "always"],
        "space-infix-ops": "error",
        "spaced-comment": ["error", "always"],

        "keyword-spacing": ["error", {
            before: true,
            after: true,
        }],

        "template-curly-spacing": ["error", "never"],
        "semi-spacing": "error",
        strict: "error",
        "node/no-missing-import": "error",
    },
}];
