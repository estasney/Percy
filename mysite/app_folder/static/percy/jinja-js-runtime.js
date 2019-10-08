function runtime(data, opts) {
    var defaults = {
        autoEscape: 'html'
    };
    var _toString = Object.prototype.toString;
    var _hasOwnProperty = Object.prototype.hasOwnProperty;
    var toString = function (val) {
        if (val == null) return '';
        return (typeof val.toString == 'function') ? val.toString() : _toString.call(val);
    };
    var extend = function (dest, src) {
        Object.keys(src).forEach(function (key) {
            dest[key] = src[key];
        });
        return dest;
    };
    var get = function () {
        var val, n = arguments[0],
            c = stack.length;
        while (c--) {
            val = stack[c][n];
            if (typeof val != 'undefined') break;
        }
        for (var i = 1, len = arguments.length; i < len; i++) {
            if (val == null) continue;
            n = arguments[i];
            val = (_hasOwnProperty.call(val, n)) ? val[n] : (typeof val._get == 'function' ? (val[n] = val._get(n)) : null);
        }
        return (val == null) ? null : val;
    };
    var set = function (n, val) {
        stack[stack.length - 1][n] = val;
    };
    var push = function (ctx) {
        stack.push(ctx || {});
    };
    var pop = function () {
        stack.pop();
    };
    var write = function (str) {
        output.push(str);
    };
    var filter = function (val) {
        for (var i = 1, len = arguments.length; i < len; i++) {
            var arr = arguments[i],
                name = arr[0],
                filter = filters[name];
            if (filter) {
                arr[0] = val;
                val = filter.apply(data, arr);
            } else {
                throw new Error('Invalid filter: ' + name);
            }
        }
        if (opts.autoEscape && name != opts.autoEscape && name != 'safe') {
            val = filters[opts.autoEscape].call(data, val);
        }
        output.push(val);
    };
    var each = function (obj, loopvar, fn1, fn2) {
        if (obj == null) return;
        var arr = Array.isArray(obj) ? obj : Object.keys(obj),
            len = arr.length;
        var ctx = {
            loop: {
                length: len,
                first: arr[0],
                last: arr[len - 1]
            }
        };
        push(ctx);
        for (var i = 0; i < len; i++) {
            extend(ctx.loop, {
                index: i + 1,
                index0: i
            });
            fn1(ctx[loopvar] = arr[i]);
        }
        if (len == 0 && fn2) fn2();
        pop();
    };
    var block = function (fn) {
        push();
        fn();
        pop();
    };
    var render = function () {
        return output.join('');
    };
    data = data || {};
    opts = extend(defaults, opts || {});
    var filters = extend({
        html: function (val) {
            return toString(val)
                .split('&').join('&amp;')
                .split('<').join('&lt;')
                .split('>').join('&gt;')
                .split('"').join('&quot;');
        }, safe: function (val) {
            return val;
        }
    }, opts.filters || {});
    var stack = [Object.create(data || {})], output = [];
    return {
        get: get, set: set, push: push, pop: pop, write: write, filter: filter, each: each, block: block, render: render
    };
}
