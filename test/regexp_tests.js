const fs = require('fs');
const _ = require('lodash');
const tape = require('tape');

const filename = process.argv[2];

// this function matches the behavior of row_fxn_regexp in the machine, with the
// addition of trimming return values to match behavior later in the machine
function getActualValue(matcher, replace) {
  // if a match group was specified, return it trimmed
  if (replace) {
    return matcher[replace].trim();
  }

  // otherwise, return the trimmed concatenation of all the matched groups
  return matcher.slice(1).join('').trim();

}

fs.readFile(filename, (err, data) => {
  const source = JSON.parse(data);

  if (!_.get(source.test, 'enabled', true)) {
    console.log('tests disabled, exiting');
    return;
  }

  // find all the conform fields that utilize the regexp function and compile
  // them for later.  The output of this is an object keyed on the regexp fields.
  const fields_with_regexp = Object.keys(source.conform).reduce((acc, curr) => {
    if (_.isObject(source.conform[curr]) && source.conform[curr]['function'] === 'regexp') {
      acc[curr] = {
        // which field to use from the test inputs blob
        input_field: source.conform[curr].field,
        regexp: new RegExp(source.conform[curr].pattern)
      };

      if (source.conform[curr].replace) {
        // "$1" -> "1"
        acc[curr].replace = source.conform[curr].replace.substr(1);
      }

    }
    return acc;

  }, {});

  // iterate the tests, validating each
  source.test.tests.forEach((test) => {
    tape.test(`testing '${test.description}'`, function(t) {
      // iterate the conform fields using regexp
      Object.keys(fields_with_regexp).forEach((field) => {
        // figure out which input value to use from the inputs blob
        const input_value = test.inputs[fields_with_regexp[field].input_field];

        // the regexp to match with
        const regexp = fields_with_regexp[field].regexp;

        // the specific match group to use, if any
        const replace = fields_with_regexp[field].replace;

        const matcher = input_value.match(regexp);
        const actual_value = getActualValue(matcher, replace);
        const expected_value = test.expected[field];

        t.equals(actual_value, expected_value,
            `${field} field: expected '${expected_value}' from input '${input_value}'`);

      });

      t.end();

    });

  });


});
