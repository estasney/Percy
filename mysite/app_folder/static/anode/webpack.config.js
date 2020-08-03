const {CleanWebpackPlugin} = require('clean-webpack-plugin');
const CopyPlugin = require("copy-webpack-plugin");
let webpack = require("webpack");
let path = require("path");

module.exports ={
    mode: 'production',
    devtool: 'source-map',
    entry: {
        labelApp: ['./src/js/labels.jsx'],
        projectLabelApp: ['./src/js/projectlabels.jsx'],
        vendor: ['./src/js/vendor.js']
    },
    output: {
        path: path.resolve('../assets/anode/js'),
        filename: '[name].[hash:8].min.js'
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: ['/node_modules/'],
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-react']
                    }
                }
            }
        ]
    },

    plugins: [
        new webpack.ProvidePlugin({
            "$": 'jquery',
            "jQuery": "jquery",
            "window.jQuery": "jquery"

        }),
        new CopyPlugin({
            patterns: [
                {
                    from: "./src/css/",
                    to: "../css/[name].[hash].[ext]",
                    toType: 'template'
                }
            ]
        }),
        new CleanWebpackPlugin()
    ]
}

