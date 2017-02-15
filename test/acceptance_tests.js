const fs = require('fs');
const _ = require('lodash');
const tape = require('tape');
const glob = require('glob');

// this function matches the behavior of row_fxn_regexp in the machine, with the
// addition of trimming return values to match behavior later in the machine
function getActualValue(matcher, replace) {
  // if a replace was specified, replace the matched groups
  // eg - if matched groups are ["abc", "a", "c"] and replace is "$1:$2"
  //      then the output is "a:c"
  if (replace) {
    return matcher.reduce((acc, curr, idx) => {
      // ignore the first matched group since it's the entire string
      return idx === 0 ? acc : acc.replace(`$${idx}`, curr);
    }, replace);

  }

  // otherwise, return the trimmed concatenation of all the matched groups
  return matcher.slice(1).join('').trim();

}

function shouldRunAcceptanceTests(source) {
  return source.test && // return false if there's no 'test' blob
          _.get(source.test, 'enabled', true) && // default 'enabled' to true
          _.get(source.test, 'acceptance-tests', []).length > 0;
}

// iterate all the source files
glob.sync('sources/**/*.json').forEach((filename) => {
  fs.readFile(filename, (err, data) => {
    const source = JSON.parse(data);

    if (!shouldRunAcceptanceTests(source)) {
      return;
    }

    // find all the conform fields that utilize the regexp function and compile
    // them for later.  The output of this is an object keyed on the regexp fields.
    const fields_with_regexp = Object.keys(source.conform).reduce((acc, curr) => {
      if (_.isObject(source.conform[curr]) && source.conform[curr]['function'] === 'regexp') {
        acc[curr] = {
          // which field to use from the test inputs blob
          input_field: source.conform[curr].field,
          regexp: new RegExp(source.conform[curr].pattern),
          replace: source.conform[curr].replace
        };

      }
      return acc;

    }, {});

    // iterate the tests, validating each
    source.test['acceptance-tests'].forEach((acceptanceTest) => {
      tape.test(`testing '${acceptanceTest.description}'`, (t) => {

        // iterate the conform fields that use the regexp function
        Object.keys(fields_with_regexp).forEach((field) => {

          // figure out which input value to use from the inputs blob
          const input_value = acceptanceTest.inputs[fields_with_regexp[field].input_field];
          const expected_value = acceptanceTest.expected[field];

          // run test only if test has input and expected value for this field
          if (input_value && expected_value) {
            // the compiled regexp to match with
            const regexp = fields_with_regexp[field].regexp;

            // the specific match group(s) to use, if any
            const replace = fields_with_regexp[field].replace;

            // run the regex against the input value
            const actual_value = getActualValue(input_value.match(regexp), replace);

            t.equals(actual_value, expected_value,
                `${field} field: expected '${expected_value}' from input '${input_value}'`);

          }

        });

        t.end();

      });

    });

  });

});
