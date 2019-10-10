export function runtime(data, opts) {
    const defaults = {
        autoEscape: 'html'
    };
    const _toString = Object.prototype.toString;
    const _hasOwnProperty = Object.prototype.hasOwnProperty;
    let toString = function (val) {
        if (val == null) return '';
        return (typeof val.toString == 'function') ? val.toString() : _toString.call(val);
    };
    let extend = function (dest, src) {
        Object.keys(src).forEach(function (key) {
            dest[key] = src[key];
        });
        return dest;
    };
    let get = function () {
        let val, n = arguments[0],
            c = stack.length;
        while (c--) {
            val = stack[c][n];
            if (typeof val != 'undefined') break;
        }
        for (let i = 1, len = arguments.length; i < len; i++) {
            if (val == null) continue;
            n = arguments[i];
            val = (_hasOwnProperty.call(val, n)) ? val[n] : (typeof val._get == 'function' ? (val[n] = val._get(n)) : null);
        }
        return (val == null) ? null : val;
    };
    let set = function (n, val) {
        stack[stack.length - 1][n] = val;
    };
    let push = function (ctx) {
        stack.push(ctx || {});
    };
    let pop = function () {
        stack.pop();
    };
    let write = function (str) {
        output.push(str);
    };
    let filter = function (val) {
        for (let i = 1, len = arguments.length; i < len; i++) {
            let arr = arguments[i],
                name = arr[0],
                filter = filters[name];
            if (filter) {
                arr[0] = val;
                val = filter.apply(data, arr);
            } else {
                throw new Error('Invalid filter: ' + name);
            }
        }
        if (opts.autoEscape && name !== opts.autoEscape && name !== 'safe') {
            val = filters[opts.autoEscape].call(data, val);
        }
        output.push(val);
    };
    let each = function (obj, loopvar, fn1, fn2) {
        if (obj == null) return;
        let arr = Array.isArray(obj) ? obj : Object.keys(obj),
            len = arr.length;
        let ctx = {
            loop: {
                length: len,
                first: arr[0],
                last: arr[len - 1]
            }
        };
        push(ctx);
        for (let i = 0; i < len; i++) {
            extend(ctx.loop, {
                index: i + 1,
                index0: i
            });
            fn1(ctx[loopvar] = arr[i]);
        }
        if (len == 0 && fn2) fn2();
        pop();
    };
    let block = function (fn) {
        push();
        fn();
        pop();
    };
    let render = function () {
        return output.join('');
    };
    data = data || {};
    opts = extend(defaults, opts || {});
    let filters = extend({
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
    let stack = [Object.create(data || {})], output = [];
    return {
        get: get, set: set, push: push, pop: pop, write: write, filter: filter, each: each, block: block, render: render
    };
}
