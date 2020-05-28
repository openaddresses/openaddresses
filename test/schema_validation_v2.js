const tape = require('tape');
const request = require('request');
const Ajv = require('ajv');
const schema = require('../schema/source_schema_v2.json');

const ajv = new Ajv({
    schemaId: 'id'
});

ajv.addMetaSchema(require('ajv/lib/refs/json-schema-draft-04.json'), "http://json-schema.org/draft-04/schema#");
ajv.addMetaSchema(require('./geojson.json'), "http://json.schemastore.org/geojson#/definitions/geometry");
testSchemaItself(ajv.compile(schema));

const nonStringValues = [null, 17, {}, [], true];
const nonBooleanValues = [null, 17, {}, [], 'string'];
const nonObjectValues = [null, 17, [], true, 'string'];
const nonArrayValues = [null, 17, {}, true, 'string'];
const nonIntegerValues = [null, 17.3, {}, [], true, 'string'];
const nonStringOrIntegerValues = [null, 17.3, {}, [], true];

// convenience function that looks for an additionalProperty error condition
// anywhere in the errors array
function isAdditionalPropertyError(validate, dataPath, property) {
    if (!validate.errors) return false;

    return validate.errors.some(err => {
        return err.keyword === 'additionalProperties' &&
            err.dataPath === dataPath &&
            err.params.additionalProperty === property;
    });

}

// convenience function that looks for an missingProperty error condition
// anywhere in the errors array
function isMissingPropertyError(validate, dataPath, fieldName) {
    if (!validate.errors) return false;

    return validate.errors.some(err => {
        return err.dataPath === dataPath &&
            err.params.missingProperty === fieldName
    });

}

function isError(keyword, validate, dataPath) {
    if (!validate.errors) return false;

    return validate.errors.some(err => {
        return err.keyword === keyword &&
            err.dataPath === dataPath
    });

}

// convenience methods for different error types
const isEnumValueError = isError.bind(null, 'enum');
const isTypeError = isError.bind(null, 'type');
const isMinItemsError = isError.bind(null, 'minItems');
const isMaximumValueError = isError.bind(null, 'maximum');
const isMinimumValueError = isError.bind(null, 'minimum');
const isPatternError = isError.bind(null, 'pattern');
const isOneOfError = isError.bind(null, 'oneOf');
const isFormatError = isError.bind(null, 'format');

function testSchemaItself(validate) {
    tape('test schema itself', (test) => {
        test.test('bare minimum source should pass', (t) => {
            ['http', 'ftp', 'ESRI'].forEach((protocol) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            name: 'county',
                            protocol: protocol,
                            data: 'http://xyz.com/'
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.ok(valid, `protocol ${protocol} should pass`);
                console.error(validate.errors);

            });

            t.end();

        });

        test.test('unknown property should fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        name: 'county',
                        data: 'http://xyz.com/',
                        unknown_property: 'value'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'protocol-less source should fail');
            t.ok(isAdditionalPropertyError(validate, '.layers.addresses[0]', 'unknown_property'), JSON.stringify(validate.errors));

            t.end();

        });

        test.test('protocol other than http/ftp/ESRI should fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        name: 'county',
                        protocol: 'non-http/ftp/ESRI',
                        data: 'http://xyz.com/'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'non-http/ftp/ESRI protocol should fail');
            t.ok(isEnumValueError(validate, '.layers.addresses[0].protocol'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('source without protocol should fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        name: 'county',
                        data: 'http://xyz.com/'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'protocol-less source should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0]', 'protocol'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('source without name should fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        data: 'http://xyz.com/'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'name-less source should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0]', 'name'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string data value should fail', (t) => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            name: 'county',
                            protocol: 'http',
                            data: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string data value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].data'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string data value should not fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        name: 'county',
                        protocol: 'http',
                        data: 'http://xyz.com/'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string data value should not fail');
            t.end();

        });

        test.test('non-string website value should fail', (t) => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            name: 'county',
                            protocol: 'http',
                            data: 'http://xyz.com/',
                            website: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string website value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].website'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string website value should not fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        website: 'this is a string'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string website value should not fail');
            t.end();

        });

        test.test('non-string email value should fail', (t) => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            email: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string email value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].email'), JSON.stringify(validate.errors));

            });
            t.end();

        });

        test.test('non-email-formatted email field should fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        email: 'this is not a valid email address'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'non-email email value should fail');
            t.ok(isFormatError(validate, '.layers.addresses[0].email', JSON.stringify(validate.errors)));
            t.end();

        });

        test.test('email-formatted email field should not fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        email: 'me@example.com'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'email-formatted email value should not fail');
            t.end();

        });

        test.test('non-string compression should fail', (t) => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            compression: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string compression value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].compression'), JSON.stringify(validate.errors));
            });

            t.end();

        });

        test.test('non-"zip" compression value should fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        compression: 'this value is not "zip"'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'non-"zip" compression value should fail');
            t.ok(isEnumValueError(validate, '.layers.addresses[0].compression'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('"zip" compression value should not fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        compression: 'zip'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, '"zip" compression value should not fail');
            t.end();

        });

        test.test('non-string attribution should fail', (t) => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            attribution: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string attribution value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].attribution'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string attribution value should not fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        attribution: 'this is a string'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string attribution value should not fail');
            t.end();

        });

        test.test('non-string language should fail', (t) => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            language: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string language value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].language'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-2- or 3-letter string language should fail', (t) => {
            ['a', 'a1', '1a', 'a a', 'aaaa'].forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            language: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string language value should fail');
                t.ok(isPatternError(validate, '.layers.addresses[0].language'), JSON.stringify(validate.errors));
            });

            t.end();

        });

        test.test('case-insensitive 2- or 3-letter string language should not fail', (t) => {
            ['aa', 'Aa', 'aA', 'AA', 'aaa', 'en', 'gb', 'lld'].forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            language: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.ok(valid, '2- or 3-letter string language value should not fail');

            });

            t.end();

        });

        test.test('non-boolean skip should fail', (t) => {
            nonBooleanValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            skip: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-boolean skip value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].skip'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('boolean skip should not fail', (t) => {
            [true, false].forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            skip: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.ok(valid, 'boolean skip value should not fail');

            });

            t.end();

        });

        test.test('non-string/integer year should fail', (t) => {
            [null, 17.3, {}, [], true].forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            year: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string/integer year value should fail');
                t.ok(isOneOfError(validate, '.layers.addresses[0].year'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string/integer year should not fail', (t) => {
            [17, 'string'].forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            year: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.ok(valid, 'string/integer year value should not fail');

            });

            t.end();

        });

        test.test('non-string/object note should fail', (t) => {
            [null, 17, [], true].forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            note: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string/object note value should fail');
                t.ok(isOneOfError(validate, '.layers.addresses[0].note'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string/integer note should not fail', (t) => {
            [{}, 'string'].forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            note: value
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.ok(valid, 'string/object note value should not fail');

            });

            t.end();

        });

    });

    tape('conform tests', test => {
        test.test('non-string format should fail', t => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string format value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.format'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('unsupported format should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'unsupported format',
                            number: 'number field',
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'non-integer note value should fail');
            t.ok(isEnumValueError(validate, '.layers.addresses[0].conform.format'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('supported format values should not fail', t => {
            ['geojson', 'shapefile', 'shapefile-polygon', 'gdb', 'xml', 'csv'].forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.ok(valid, 'supported conform.format value should not fail');

            });

            t.end();

        });

        test.test('non-string addrtype should fail', t => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                addrtype: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string addrtype value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.addrtype'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-integer accuracy should fail', t => {
            nonIntegerValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                accuracy: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-integer accuracy value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.accuracy'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('accuracy less than 1 should fail', t => {
            [-1, 0].forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: 'street field',
                                accuracy: value
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'value less than 1 should fail');
                t.ok(isMinimumValueError(validate, '.layers.addresses[0].conform.accuracy'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('accuracy greater than 5 should fail', t => {
            [6, 7].forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: 'street field',
                                accuracy: value
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-integer note value should fail');
                t.ok(isMaximumValueError(validate, '.layers.addresses[0].conform.accuracy'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string srs should fail', t => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                srs: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string srs value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.srs'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('srs not matching EPSG:# format should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            srs: 'EPSG:abcd',
                            number: 'number field',
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'srs value not matching pattern should fail');
            t.ok(isPatternError(validate, '.layers.addresses[0].conform.srs'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string file should fail', t => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'csv',
                                file: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-integer/string file value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.file'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string/integer layer should fail', t => {
            nonStringOrIntegerValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'csv',
                                layer: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-integer/string layer value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.layer'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string encoding should fail', t => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'csv',
                                encoding: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-integer note value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.encoding'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string csvsplit should fail', t => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'csv',
                                csvsplit: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-integer note value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.csvsplit'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-integer headers should fail', t => {
            nonIntegerValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'csv',
                                headers: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-integer note value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.headers'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('headers less than -1 should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'csv',
                            headers: -2,
                            number: 'number field',
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'value less than 1 should fail');
            t.ok(isMinimumValueError(validate, '.layers.addresses[0].conform.headers'), JSON.stringify(validate.errors));
            t.end();


        });

        test.test('non-integer skiplines should fail', t => {
            nonIntegerValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'csv',
                                skiplines: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-integer note value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.skiplines'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('skiplines less than 1 should fail', t => {
            [-1, 0].forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'csv',
                                skiplines: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'value less than 1 should fail');
                t.ok(isMinimumValueError(validate, '.layers.addresses[0].conform.skiplines'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string notes should fail', t => {
            nonStringValues.forEach((value) => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                notes: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string note value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.notes'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string/array/object id should fail', t => {
            [null, 17, true].forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                id: value,
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string/array/object id value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.id'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('id array containing non-string elements should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                id: ['field1', value, 'field2'],
                                number: 'number field',
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string elements in id array should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.id'), JSON.stringify(validate.errors));

            });

            t.end();

        });

    });

    tape('coverage tests', test => {
        test.test('missing coverage property should fail', t => {
            const source = {
                schema: 2,
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing coverage property should fail');
            t.ok(isMissingPropertyError(validate, '', 'coverage'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-object coverage should fail', t => {
            nonObjectValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: value,
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/'
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-object coverage should fail');
                t.ok(isTypeError(validate, '.coverage'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('missing country should fail', t => {
            const source = {
                schema: 2,
                coverage: { },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/'
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'coverage missing country should fail');
            t.ok(isMissingPropertyError(validate, '.coverage', 'country'), JSON.stringify(validate.errors));
            t.end();

        });

    });

    tape('prefixed_number function tests', test => {
        test.test('missing field property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'prefixed_number'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing field value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'field'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string field value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'prefixed_number',
                                    field: value
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string field value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.field'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string field value should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'prefixed_number',
                                field: 'number field'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string conform.number.field value should not fail');
            t.end();

        });

        test.test('unknown property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'prefixed_number',
                                field: 'number field',
                                unknown_property: 'value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'unknown property in prefixed_number should fail');
            t.ok(isAdditionalPropertyError(validate, '.layers.addresses[0].conform.number', 'unknown_property'), JSON.stringify(validate.errors));
            t.end();

        });

    });

    tape('postfixed_street function tests', test => {
        test.test('missing field property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: {
                                function: 'postfixed_street'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing field value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.street', 'field'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string field value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: {
                                    function: 'postfixed_street',
                                    field: value
                                }
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string field value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.street.field'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string field value should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: {
                                function: 'postfixed_street',
                                field: 'street field'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string conform.street.field value should not fail');
            t.end();

        });

        test.test('non-boolean may_contain_units should fail', t => {
            nonBooleanValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: {
                                    function: 'postfixed_street',
                                    field: 'street field',
                                    may_contain_units: value
                                }
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-boolean may_contain_units value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.street.may_contain_units'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('boolean may_contain_units should not fail', t => {
            [true, false].forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'http',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: {
                                    function: 'postfixed_street',
                                    field: 'street field',
                                    may_contain_units: value
                                }
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.ok(valid, 'boolean may_contain_units value should not fail');

            });

            t.end();

        });

        test.test('unknown property should fail', (t) => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: {
                                function: 'postfixed_street',
                                field: 'street field',
                                unknown_property: 'value'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'unknown property in postfixed_street should fail');
            t.ok(isAdditionalPropertyError(validate, '.layers.addresses[0].conform.street', 'unknown_property'), JSON.stringify(validate.errors));
            t.end();

        });

    });

    tape('postfixed_unit function tests', test => {
        test.test('missing field property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: 'street field',
                            unit: {
                                function: 'postfixed_unit'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing field value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.unit', 'field'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string field value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: 'street field',
                                unit: {
                                    function: 'postfixed_unit',
                                    field: value
                                }
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string field value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.unit.field'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string field value should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: 'street field',
                            unit: {
                                function: 'postfixed_unit',
                                field: 'street field'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string conform.unit.field value should not fail');
            t.end();

        });

        test.test('unknown property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: 'street field',
                            unit: {
                                function: 'postfixed_unit',
                                field: 'unit field',
                                unknown_property: 'value'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'unknown property in postfixed_unit should fail');
            t.ok(isAdditionalPropertyError(validate, '.layers.addresses[0].conform.unit', 'unknown_property'), JSON.stringify(validate.errors));
            t.end();

        });

    });

    tape('remove_prefix function tests', test => {
        test.test('missing field should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'remove_prefix',
                                field: 'field value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing field_to_remove value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'field_to_remove'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string field value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: {
                                    function: 'remove_prefix',
                                    field: value,
                                    field_to_remove: 'field to remove'
                                }
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string field value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.street.field'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('missing field_to_remove should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'remove_prefix',
                                field_to_remove: 'field_to_remove value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing field value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'field'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string field_to_remove value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: {
                                    function: 'remove_prefix',
                                    field: 'field value',
                                    field_to_remove: value
                                }
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string field value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.street.field_to_remove'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string field and field_to_remove values should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: {
                                function: 'remove_prefix',
                                field: 'field',
                                field_to_remove: 'field to remove'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string conform.street.field value should not fail');
            t.end();

        });

        test.test('unknown property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: {
                                function: 'remove_prefix',
                                field: 'unit field',
                                unknown_property: 'value'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'unknown property in postfixed_unit should fail');
            t.ok(isAdditionalPropertyError(validate, '.layers.addresses[0].conform.street', 'unknown_property'), JSON.stringify(validate.errors));
            t.end();

        });

    });

    tape('remove_postfix function tests', test => {
        test.test('missing field should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'remove_postfix',
                                field_to_remove: 'field_to_remove value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing field_to_remove value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'field'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string field value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: {
                                    function: 'remove_postfix',
                                    field: value,
                                    field_to_remove: 'field to remove'
                                }
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string field value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.street.field'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('missing field_to_remove should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'remove_postfix',
                                field: 'field value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing field value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'field_to_remove'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string field_to_remove value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: 'number field',
                                street: {
                                    function: 'remove_postfix',
                                    field: 'field value',
                                    field_to_remove: value
                                }
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string field value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.street.field_to_remove'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string field and field_to_remove values should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: {
                                function: 'remove_postfix',
                                field: 'field',
                                field_to_remove: 'field to remove'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string conform.street.field value should not fail');
            t.end();

        });

        test.test('unknown property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: 'number field',
                            street: {
                                function: 'remove_postfix',
                                field: 'unit field',
                                unknown_property: 'value'
                            }
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'unknown property in postfixed_unit should fail');
            t.ok(isAdditionalPropertyError(validate, '.layers.addresses[0].conform.street', 'unknown_property'), JSON.stringify(validate.errors));
            t.end();

        });

    });

    tape('regexp function tests', test => {
        test.test('missing field value should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'regexp',
                                pattern: 'pattern value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing field value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'field'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('missing pattern value should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'regexp',
                                field: 'field value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing pattern value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'pattern'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string field value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'regexp',
                                    field: value,
                                    pattern: 'pattern value'
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: [],
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string field value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.field'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string pattern value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'regexp',
                                    field: 'field value',
                                    pattern: value
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string pattern value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.pattern'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string replace value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'regexp',
                                    field: 'field value',
                                    pattern: 'pattern value',
                                    replace: value
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string replace value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.replace'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('string field and pattern w/o replace should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'regexp',
                                field: 'field value',
                                pattern: 'pattern value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string conform.street.field/pattern value should not fail');
            t.end();

        });

        test.test('string field, pattern, and replace should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'regexp',
                                field: 'field value',
                                pattern: 'pattern value',
                                replace: 'replace value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.ok(valid, 'string conform.street.field/pattern/replace values should not fail');
            t.end();

        });

        test.test('unknown property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'regexp',
                                field: 'field value',
                                pattern: 'pattern value',
                                unknown_property: 'value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'unknown property in regexp should fail');
            t.ok(isAdditionalPropertyError(validate, '.layers.addresses[0].conform.number', 'unknown_property'), JSON.stringify(validate.errors));
            t.end();

        });

    });

    tape('join function tests', test => {
        test.test('missing fields value should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'join'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing fields value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'fields'), JSON.stringify(validate.errors));
            t.end();


        });

        test.test('non-array fields value should fail', t => {
            nonArrayValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'join',
                                    fields: value
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: [],
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-array fields value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.fields'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('empty fields array should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'join',
                                fields: []
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: [],
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'empty fields array should fail');
            t.ok(isMinItemsError(validate, '.layers.addresses[0].conform.number.fields'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string elements of fields array should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'join',
                                    fields: ['field 1', value, 'field 2']
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string elements of fields array should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.fields[1]'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string separator value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'join',
                                    fields: ['field1', 'field2'],
                                    separator: value
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: [],
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string separator value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.separator'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-empty fields containing only strings should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'join',
                                fields: ['field 1', 'field 2']
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: [],
                }
            };

            const valid = validate(source);

            t.ok(valid, 'non-empty fields containing only strings should not fail');
            t.end();

        });

        test.test('non-empty fields containing only strings and string separator value should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'join',
                                fields: ['field 1', 'field 2'],
                                separator: 'separator value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: [],
                }
            };

            const valid = validate(source);

            t.ok(valid, 'non-empty fields containing only strings and string separator should not fail');
            t.end();

        });

        test.test('unknown property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'join',
                                fields: ['field 1', 'field 2'],
                                unknown_property: 'value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'unknown property in join should fail');
            t.ok(isAdditionalPropertyError(validate, '.layers.addresses[0].conform.number', 'unknown_property'), JSON.stringify(validate.errors));
            t.end();

        });

    });

    tape('format function tests', test => {
        test.test('missing fields value should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'format',
                                format: 'format value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
            }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing fields value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'fields'), JSON.stringify(validate.errors));
            t.end();


        });

        test.test('missing format value should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'format',
                                fields: ['field 1', 'field 2']
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'missing format value should fail');
            t.ok(isMissingPropertyError(validate, '.layers.addresses[0].conform.number', 'format'), JSON.stringify(validate.errors));
            t.end();


        });

        test.test('non-array fields value should fail', t => {
            nonArrayValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'format',
                                    fields: value,
                                    format: 'format value'
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: [],
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-array fields value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.fields'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('empty fields array should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'ESRI',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'format',
                                fields: [],
                                format: 'format value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: [],
                }
            };

            const valid = validate(source);

            t.notOk(valid, 'empty fields array should fail');
            t.ok(isMinItemsError(validate, '.layers.addresses[0].conform.number.fields'), JSON.stringify(validate.errors));
            t.end();

        });

        test.test('non-string elements of fields array should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'format',
                                    fields: ['field 1', value, 'field 2'],
                                    format: 'format value'
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string elements of fields array should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.fields[1]'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-string format value should fail', t => {
            nonStringValues.forEach(value => {
                const source = {
                    schema: 2,
                    coverage: {
                        country: 'some country'
                    },
                    layers: {
                        addresses: [{
                            protocol: 'ESRI',
                            name: 'county',
                            data: 'http://xyz.com/',
                            conform: {
                                format: 'geojson',
                                number: {
                                    function: 'format',
                                    fields: ['field1', 'field2'],
                                    format: value
                                },
                                street: 'street field'
                            }
                        }],
                        buildings: []
                    }
                };

                const valid = validate(source);

                t.notOk(valid, 'non-string format value should fail');
                t.ok(isTypeError(validate, '.layers.addresses[0].conform.number.format'), JSON.stringify(validate.errors));

            });

            t.end();

        });

        test.test('non-empty fields containing only strings and string format should not fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'format',
                                fields: ['field 1', 'field 2'],
                                format: 'format value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: [],
                }
            };

            const valid = validate(source);

            t.ok(valid, 'non-empty fields containing only strings and string format should not fail');
            t.end();

        });

        test.test('unknown property should fail', t => {
            const source = {
                schema: 2,
                coverage: {
                    country: 'some country'
                },
                layers: {
                    addresses: [{
                        protocol: 'http',
                        name: 'county',
                        data: 'http://xyz.com/',
                        conform: {
                            format: 'geojson',
                            number: {
                                function: 'format',
                                fields: ['field 1', 'field 2'],
                                format: 'format value',
                                unknown_property: 'value'
                            },
                            street: 'street field'
                        }
                    }],
                    buildings: []
                }

            };

            const valid = validate(source);

            t.notOk(valid, 'unknown property in format should fail');
            t.ok(isAdditionalPropertyError(validate, '.layers.addresses[0].conform.number', 'unknown_property'), JSON.stringify(validate.errors));
            t.end();

        });
    });
}

