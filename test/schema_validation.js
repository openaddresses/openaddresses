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
      callback(err || new Error('Loading error: ' + res.statusCode));
    } else {
      callback(null, JSON.parse(body));
    }
  });
}

// convenience function that looks for an additionalProperty error condition
// anywhere in the errors array
function isAdditionalPropertyError(validate, property) {
  if (!validate.errors) return false;

  return validate.errors.some(function(err) {
    return err.params.additionalProperty === property;
  });
}

// convenience function that looks for an incorrect type error condition
// anywhere in the errors array
function isEnumValueError(validate, property) {
  if (!validate.errors) return false;

  return validate.errors.some(function(err) {
    return err.schemaPath === '#/properties/' + property + '/enum';
  });
}

// convenience function that looks for an missingProperty error condition
// anywhere in the errors array
function isMissingPropertyError(validate, type) {
  if (!validate.errors) return false;

  return validate.errors.some(function(err) {
    return err.params.missingProperty === type;
  });
}

// convenience function that looks for an type error condition
// anywhere in the errors array
function isTypeError(validate, property) {
  if (!validate.errors) return false;

  return validate.errors.some(function(err) {
    return err.schemaPath === '#/properties/' + property + '/type';
  });
}

function testSchemaItself(validate) {
  test('bare minimum source should pass', function(t) {
    ['http', 'ftp', 'ESRI'].forEach(function(type) {
      var source = {
        coverage: {
          country: 'some country'
        },
        type: type,
        data: 'http://xyz.com/'
      };

      var valid = validate(source);

      t.ok(valid, 'type ' + type + ' should pass');

    });

    t.end();

  });

  test.test('unknown field should fail', function(t) {
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

  test.test('type other than http/ftp/ESRI should fail', function(t) {
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

  test.test('source without type should fail', function(t) {
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

  test.test('non-string data value should fail', function(t) {
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

  test.test('non-string website value should fail', function(t) {
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

}
