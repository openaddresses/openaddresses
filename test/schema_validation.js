var test = require('tape').test;
var request = require('request');
var Ajv = require('ajv');
var schema = require('../schema/source_schema.json');

var ajv = new Ajv( { loadSchema: loadSchema } );

// the schema contains a remote schema for geojson so it must be loaded async
ajv.compileAsync(schema, function (err, validate) {
  if (err) return;
  testSchemaItself(validate);
});

// this function instructs Ajv on how to load remote sources
function loadSchema(uri, callback) {
  request.get({url:uri}, function(err, res, body) {
    if (err || res.statusCode >= 400) {
      callback(err || new Error(`Loading error: ${res.statusCode}`));
    } else {
      callback(null, JSON.parse(body));
    }
  });
}

// convenience function that looks for an additionalProperty error condition
// anywhere in the errors array
function isAdditionalPropertyError(validate, property) {
  if (!validate.errors) return false;

  return validate.errors.some((err) => {
    return err.params.additionalProperty === property;
  });
}

// convenience function that looks for an incorrect type error condition
// anywhere in the errors array
function isEnumValueError(validate, property) {
  if (!validate.errors) return false;

  return validate.errors.some((err) => {
    return err.schemaPath === `#/properties/${property}/enum`;
  });
}

// convenience function that looks for an missingProperty error condition
// anywhere in the errors array
function isMissingPropertyError(validate, type) {
  if (!validate.errors) return false;

  return validate.errors.some((err) => {
    return err.params.missingProperty === type;
  });
}

// convenience function that looks for an type error condition
// anywhere in the errors array
function isTypeError(validate, property) {
  if (!validate.errors) return false;

  return validate.errors.some((err) => {
    return err.schemaPath === `#/properties/${property}/type`;
  });
}

function isOneOfError(validate, property) {
  if (!validate.errors) return false;

  return validate.errors.some((err) => {
    return err.schemaPath === `#/properties/${property}/oneOf`;
  });
}

function isFormatError(validate, property) {
  if (!validate.errors) return false;

  return validate.errors.some((err) => {
    return err.schemaPath === `#/properties/${property}/format`;
  });
}

function isPatternError(validate, property) {
  if (!validate.errors) return false;

  return validate.errors.some((err) => {
    return err.schemaPath === `#/properties/${property}/pattern`;
  });
}

function testSchemaItself(validate) {
  test('bare minimum source should pass', (t) => {
    ['http', 'ftp', 'ESRI'].forEach((type) => {
      var source = {
        coverage: {
          country: 'some country'
        },
        type: type,
        data: 'http://xyz.com/'
      };

      var valid = validate(source);

      t.ok(valid, `type ${type} should pass`);

    });

    t.end();

  });

  test.test('unknown field should fail', (t) => {
    var source = {
      coverage: {
        country: 'some country'
      },
      type: 'http',
      data: 'http://xyz.com/',
      unknown_field: 'value'
    };

    var valid = validate(source);

    t.notOk(valid, 'type-less source should fail');
    t.ok(isAdditionalPropertyError(validate, 'unknown_field'), JSON.stringify(validate.errors));
    t.end();

  });

  test.test('type other than http/ftp/ESRI should fail', (t) => {
    var source = {
      coverage: {
        country: 'some country'
      },
      type: 'non-http/ftp/ESRI',
      data: 'http://xyz.com/'
    };

    var valid = validate(source);

    t.notOk(valid, 'non-http/ftp/ESRI type should fail');
    t.ok(isEnumValueError(validate, 'type'), JSON.stringify(validate.errors));
    t.end();

  });

  test.test('source without type should fail', (t) => {
    var source = {
      coverage: {
        country: 'some country'
      },
      data: 'http://xyz.com/'
    };

    var valid = validate(source);

    t.notOk(valid, 'type-less source should fail');
    t.ok(isMissingPropertyError(validate, 'type'), JSON.stringify(validate.errors));
    t.end();

  });

  test.test('non-string data value should fail', (t) => {
    var source = {
      type: 'http',
      coverage: {
        country: 'some country'
      },
      data: 17
    };

    var valid = validate(source);

    t.notOk(valid, 'non-string data value should fail');
    t.ok(isTypeError(validate, 'data'), JSON.stringify(validate.errors));
    t.end();

  });

  test.test('string data value should not fail', (t) => {
    var source = {
      type: 'http',
      coverage: {
        country: 'some country'
      },
      data: 'http://xyz.com/'
    };

    var valid = validate(source);

    t.ok(valid, 'string data value should not fail');
    t.end();

  });

  test.test('non-string website value should fail', (t) => {
    var source = {
      type: 'http',
      coverage: {
        country: 'some country'
      },
      data: 'http://xyz.com/',
      website: 17
    };

    var valid = validate(source);

    t.notOk(valid, 'non-string website value should fail');
    t.ok(isTypeError(validate, 'website'), JSON.stringify(validate.errors));
    t.end();

  });

  test.test('string website value should not fail', (t) => {
    var source = {
      type: 'http',
      coverage: {
        country: 'some country'
      },
      data: 'http://xyz.com/',
      website: 'this is a string'
    };

    var valid = validate(source);

    t.ok(valid, 'string website value should not fail');
    t.end();

  });

  test.test('non-string email value should fail', (t) => {
    [null, 17, {}, [], true].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        email: value
      };

      var valid = validate(source);

      t.notOk(valid, 'non-string email value should fail');
      t.ok(isTypeError(validate, 'email'), JSON.stringify(validate.errors));

    });
    t.end();

  });

  test.test('non-email-formatted email field should fail', (t) => {
    var source = {
      type: 'http',
      coverage: {
        country: 'some country'
      },
      data: 'http://xyz.com/',
      email: 'this is not a valid email address'
    };

    var valid = validate(source);

    t.notOk(valid, 'non-email email value should fail');
    t.ok(isFormatError(validate, 'email', JSON.stringify(validate.errors)));
    t.end();

  });

  test.test('email-formatted email field should not fail', (t) => {
    var source = {
      type: 'http',
      coverage: {
        country: 'some country'
      },
      data: 'http://xyz.com/',
      email: 'me@example.com'
    };

    var valid = validate(source);

    t.ok(valid, 'email-formatted email value should not fail');
    t.end();

  });

  test.test('non-string compression should fail', (t) => {
    [null, 17, {}, [], true].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        compression: value
      };

      var valid = validate(source);

      t.notOk(valid, 'non-string email value should fail');
      t.ok(isEnumValueError(validate, 'compression'), JSON.stringify(validate.errors));

    });

    t.end();

  });

  test.test('non-"zip" compression value should fail', (t) => {
    var source = {
      type: 'http',
      coverage: {
        country: 'some country'
      },
      data: 'http://xyz.com/',
      compression: 'this value is not "zip"'
    };

    var valid = validate(source);

    t.notOk(valid, 'non-"zip" compression value should fail');
    t.ok(isEnumValueError(validate, 'compression'), JSON.stringify(validate.errors));
    t.end();

  });

  test.test('"zip" compression value should not fail', (t) => {
    var source = {
      type: 'http',
      coverage: {
        country: 'some country'
      },
      data: 'http://xyz.com/',
      compression: 'zip'
    };

    var valid = validate(source);

    t.ok(valid, '"zip" compression value should not fail');
    t.end();

  });

  test.test('non-string attribution should fail', (t) => {
    [null, 17, {}, [], true].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        attribution: value
      };

      var valid = validate(source);

      t.notOk(valid, 'non-string attribution value should fail');
      t.ok(isTypeError(validate, 'attribution'), JSON.stringify(validate.errors));

    });

    t.end();

  });

  test.test('string attribution value should not fail', (t) => {
    var source = {
      type: 'http',
      coverage: {
        country: 'some country'
      },
      data: 'http://xyz.com/',
      attribution: 'this is a string'
    };

    var valid = validate(source);

    t.ok(valid, 'string attribution value should not fail');
    t.end();

  });

  test.test('non-string language should fail', (t) => {
    [null, 17, {}, [], true].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        language: value
      };

      var valid = validate(source);

      t.notOk(valid, 'non-string language value should fail');
      t.ok(isTypeError(validate, 'language'), JSON.stringify(validate.errors));

    });

    t.end();

  });

  test.test('non-2-letter-string language should fail', (t) => {
    ['a', 'a1', '1a', 'aaa'].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        language: value
      };

      var valid = validate(source);

      t.notOk(valid, 'non-string language value should fail');
      t.ok(isPatternError(validate, 'language'), JSON.stringify(validate.errors));

    });

    t.end();

  });

  test.test('case-insensitive 2-letter-string language should not fail', (t) => {
    ['aa', 'Aa', 'aA', 'AA'].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        language: value
      };

      var valid = validate(source);

      t.ok(valid, '2-letter string language value should not fail');

    });

    t.end();

  });

  test.test('non-boolean skip should fail', (t) => {
    [null, 17, {}, [], 'string'].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        skip: value
      };

      var valid = validate(source);

      t.notOk(valid, 'non-boolean skip value should fail');
      t.ok(isTypeError(validate, 'skip'), JSON.stringify(validate.errors));

    });

    t.end();

  });

  test.test('boolean skip should not fail', (t) => {
    [true, false].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        skip: value
      };

      var valid = validate(source);

      t.ok(valid, 'boolean skip value should not fail');

    });

    t.end();

  });

  test.test('non-string/integer year should fail', (t) => {
    [null, 17.3, {}, [], true].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        year: value
      };

      var valid = validate(source);

      t.notOk(valid, 'non-string/integer year value should fail');
      t.ok(isOneOfError(validate, 'year'), JSON.stringify(validate.errors));

    });

    t.end();

  });

  test.test('string/integer year should not fail', (t) => {
    [17, 'string'].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        year: value
      };

      var valid = validate(source);

      t.ok(valid, 'string/integer year value should not fail');

    });

    t.end();

  });

  test.test('non-string/object note should fail', (t) => {
    [null, 17, [], true].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        note: value
      };

      var valid = validate(source);

      t.notOk(valid, 'non-string/object note value should fail');
      t.ok(isOneOfError(validate, 'note'), JSON.stringify(validate.errors));

    });

    t.end();

  });

  test.test('string/integer note should not fail', (t) => {
    [{}, 'string'].forEach((value) => {
      var source = {
        type: 'http',
        coverage: {
          country: 'some country'
        },
        data: 'http://xyz.com/',
        note: value
      };

      var valid = validate(source);

      t.ok(valid, 'string/object note value should not fail');

    });

    t.end();

  });

}
