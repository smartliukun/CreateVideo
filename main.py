from apify_client import ApifyClient
import json

# 用您的 Apify API 令牌初始化客户端
client = ApifyClient("")

# 设置 Actor 输入参数
run_input = {
 #   "category": "7",        # 新闻类别 ID
    "page": "0",              # 页码
    "limit": "20",            # 每页新闻数量
    "keywordName": "trump",  # 关键词
#    "author": "1510",         # 作者 ID
#    "marketAssetId": 1,       # 市场资产 ID
 #   "marketCategoryId": 1,    # 市场类别 ID
    "selectReutersPageType": "rn-get-articles-by-keyword-name",
}

# 运行 Actor 并等待完成
run = client.actor("making-data-meaningful/reuters-api").call(run_input=run_input)

# 从运行结果的数据集中获取并打印新闻条目
dataset_items = client.dataset(run["defaultDatasetId"]).iterate_items()
result= []
for item in dataset_items:
    for article in item['articles']:
        result.append(article)
        break
        #print(str(item))

json_string = json.dumps(result, indent=4)  # `indent=4` 让 JSON 格式更美观
print(json_string)


#'articlesName' = {str} 'Trump orders new tariff probe into US lumber imports'
#'articlesShortDescription' = {str} 'U.S. President Donald Trump on Saturday ordered a new trade investigation that could heap more tariffs on imported lumber, adding to existing duties on Canadian softwood lumber and 25% tariffs on all Canadian and Mexican goods due next week.'
#'articlesDescription' = {str} '[{"content":"U.S. President Donald Trump on Saturday ordered a new trade investigation that could heap more tariffs on imported lumber, adding to existing duties on Canadian softwood lumber and 25% tariffs on all Canadian and Mexican goods due next week."
#'minutesToRead' = {int} 3
#'wordCount' = {str} '583'
#'urlSupplier' = {str} '/world/us/trump-orders-new-tariff-probe-into-us-lumber-imports-2025-03-02/'
#'publishedAt' = {dict: 3} {'date': '2025-03-02 00:06:13.000000', 'timezone': 'Europe/Bucharest', 'timezone_type': 3}


