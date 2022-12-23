#!/usr/bin/env node

"use strict";

var fs = require('fs');
var csv = require('csv');
var req = require('request');
var _ = require('lodash');
var querystring = require('querystring');
var program = require('commander');

var query = {wants: ['edx_username', 'user_id', 'cwl', 'student_number']};
var buffer = [];
var usernameField;
var emailField;

program
    .version('0.0.1')
    .option('-E, --no-email', 'No email mapping', Boolean, false)
    .option('-b, --buffer-size [n]', 'Buffer size', parseInt, 10)
    .option('-t, --token [token]', 'Authentication token')
    .option('-u, --url [baseURL]', 'Base URL for IDMapping', 'http://127.0.0.1:8000/api/map')
    .arguments('<csv_file>')
    .parse(process.argv);

if (!program.args.length) {
    program.help();
}

var options = {
    method: 'GET',
    json:true,
    headers: { 'Authorization': 'Token ' + program.token }
};
var input = fs.createReadStream(program.args[0]);
var parserFinished = false;
var transformed = 0;
var parser = csv.parse({skip_empty_lines: true, columns: true, rowDelimiter: "\n"});
parser.on('finish', function() {
    parserFinished = true;
});
var transformer = csv.transform(function(record, callback) {
    // buffer program.bufferSize record and query them together
    if (!usernameField) {
        if (record.hasOwnProperty('username')) {
            usernameField = 'username';
        } else if (record.hasOwnProperty('Username')) {
            usernameField = 'Username';
        }
    }
    if (!emailField) {
        if (record.hasOwnProperty('email')) {
            emailField = 'email';
        } else if (record.hasOwnProperty('Email')) {
            emailField = 'Email';
        }
    }

    //console.error(record);
    if (!usernameField && !emailField) {
        throw new Error("File doesn't contain either username or email column!");
    }

    if (!record.hasOwnProperty(usernameField)) {
        console.error('No username found for row ' + transformed + '. Skipping...');
    } else {
        buffer.push(record);
        transformed++;
    }

    //console.error(transformed, parser.count, parser.lines);
    if (buffer.length < program.bufferSize && !(parserFinished && transformed == parser.count)) {
        callback(null, null);
        return;
    }

    var localBuffer = buffer;
    var func = this;
    buffer = [];
    query.edx_username = _.pluck(_.uniq(localBuffer, usernameField), usernameField);
    var requestParams = querystring.stringify(query);
    options.url = program.url + '?' + requestParams;

    req(options, function(error, response, body){
        if (!error && response.statusCode == 200) {
            _.each(body, function(item) {
                // it is possible to have the same username in multiple rows
                var q = {};
                q[usernameField] = item.edx_username;
                var rows = _.filter(localBuffer, q);
                _.each(rows, function(row) {
                    if (!row) {
                        console.error('Can not find row for edx username ' + item.edx_username);
                        return;
                    }
                    row.PUID = item.user_id;
                    row.CWL = item.cwl;
                    row.student_number = item.student_number;
                });
            });

            var missing = _.filter(localBuffer, function(item) {
                return !item.hasOwnProperty('PUID') || item.PUID == null;
            });
            // mapping by email
            if (missing.length > 0 && program.email && emailField) {
                var q = {
                    wants: ['user_id', 'cwl', 'student_number', 'email'],
                    email: _.pluck(missing, emailField)
                };
                options.url = program.url + '?' + querystring.stringify(q);
                req(options, function (error, response, body) {
                    if (!error && response.statusCode == 200) {
                        _.each(body, function (item) {
                            var q = {};
                            q[emailField] = item.email;
                            var row = _.find(localBuffer, q);
                            if (!row) {
                                console.log('Can not find row for email ' + item.email);
                                return;
                            }
                            row.PUID = item.user_id;
                            row.CWL = item.cwl;
                            row.student_number = item.student_number;
                        });
                    }
                    // add error parameters
                    localBuffer.unshift(error);
                    callback.apply(func, localBuffer);
                });
            } else {
                // add error parameters
                localBuffer.unshift(error);
                callback.apply(func, localBuffer);
            }
        } else {
            // add error parameters
            localBuffer.unshift(error);
            callback.apply(func, localBuffer);
        }
    });
}, {parallel: 1});

transformer.on('error', function(err){
  console.error(err.message);
});

input
    .pipe(parser)
    .pipe(transformer)
    .pipe(csv.stringify({quoted: true, header: true}))
    .pipe(process.stdout);
