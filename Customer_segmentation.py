# -*- coding: utf-8 -*-
"""P4. Notebook de l'analyse exploratoire

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1DTiN8cyVGSK4M-Dv6F4c4AK0q2up6BAN

# Project: Customer Segmentation and Clustering Analysis for Targeted Marketing Strategies

An in-depth analysis of customer segmentation using RFM metrics and various clustering algorithms. Here's a summarized overview of the key steps:

1. Data Cleaning & Exploration: I cleaned the data by handling missing values, converting data types, and merging data frames. This ensured the data was suitable for analysis.

2. RFM Segmentation: I calculated RFM metrics (Recency, Frequency, Monetary) for each customer, allowing me to segment them based on their purchasing behavior.

3. K-means Clustering: I applied the K-means algorithm to the RFM data, determining the optimal number of clusters using the Elbow method. This helped identify distinct customer groups and evaluate clustering performance.

4. DBSCAN: I explored the DBSCAN algorithm to identify clusters based on density. By varying parameters such as epsilon and minimum samples, I evaluated the resulting clusters.

5. CAH: Hierarchical clustering was performed using the AgglomerativeClustering algorithm, enabling the identification of hierarchical structures within the data.

6. GMM: Gaussian Mixture Models (GMM) were used to model the data as a mixture of Gaussian distributions, providing insights into the clustering patterns.

7. Cluster Profiling: I computed summary statistics for each cluster, such as mean, minimum, and maximum values of the RFM metrics. This allowed me to understand the behavior and purchasing patterns of customers in each group.

8. Snake Plot: Snake plots were created to visualize and compare the RFM metrics for each cluster, highlighting distinct characteristics.

9. Cluster Description: Bar plots were generated to show the distribution of customers across clusters, providing an overview of the relative sizes of each group.

10. ARI: The Adjusted Rand Index (ARI) was calculated to evaluate the stability and consistency of clustering results over time.

These analyses provided valuable insights for targeted marketing strategies and customer relationship management.

# Libraries

requirements.txt

pip install pandas
pip install numpy
pip install matplotlib
pip install seaborn
pip install sklearn
pip install yellowbrick
pip install squarify
pip install openpyxl
"""

!unzip /content/drive/MyDrive/Datasets/brazilian-ecommerce.zip
!pip install squarify
!pip install openpyxl

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import silhouette_samples, silhouette_score

from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.cluster import DBSCAN

from sklearn import metrics
from yellowbrick.cluster import KElbowVisualizer
from yellowbrick.cluster import SilhouetteVisualizer
from sklearn.preprocessing import RobustScaler,StandardScaler
from sklearn.preprocessing import PowerTransformer

import squarify
import warnings
warnings.filterwarnings("ignore")




# %matplotlib inline

"""# Helpers

### A. Global cleaning function
"""

def nettoyage(liste):

    customers_2 = liste[0].copy()
    geolocation_2  = liste[1].copy()
    order_items_2  = liste[2].copy()
    order_payments_2  = liste[3].copy()
    order_reviews_2  = liste[4].copy()
    orders_2  = liste[5].copy()
    products_2 = liste[6].copy()
    sellers_2 = liste[7].copy()
    translation_2 = liste[8].copy()

    geolocation_2.drop_duplicates(inplace=True)

    # Nan

    orders['order_delivered_customer_date'].fillna(0, inplace=True)
    products_2['product_category_name'].fillna('Unknown', inplace=True)

    # Nettoyage types:

    order_items_2['shipping_limit_date'] = order_items_2['shipping_limit_date'].astype('datetime64')
    orders_2['order_purchase_timestamp'] = orders_2['order_purchase_timestamp'].astype('datetime64')
    orders_2['order_delivered_customer_date'] = pd.to_datetime(orders_2['order_delivered_customer_date'], errors='coerce')
    orders_2['order_estimated_delivery_date'] = orders_2['order_estimated_delivery_date'].astype('datetime64')


    # Review score
    '''calcul de la moyennes des scores par ordre et suppression de doublons'''

    order_reviews_2['review_score'] = order_reviews_2['review_score'].astype('object')
    order_reviews_2 = order_reviews_2.drop(columns=['review_id', 'review_comment_title','review_comment_message',
                                                    'review_creation_date','review_answer_timestamp'])

    order_reviews_2 ["review_score"] = order_reviews_2.groupby(['order_id'])["review_score"].transform('mean')
    order_reviews_2 = order_reviews_2.drop_duplicates()

    # Payment value

    ''' calcul de la somme des payements par ordre et suppression de doublons'''

    order_payments_2 = order_payments_2.drop(columns = ['payment_sequential', 'payment_type','payment_installments'])

    order_payments_2 ["payment_value"] = order_payments_2.groupby(['order_id'])["payment_value"].transform('sum')
    order_payments_2 = order_payments_2.drop_duplicates()

    # Merge des catégories de produits
    products_2 = pd.merge(products_2, translation_2).drop(['product_category_name'], axis=1)

    # fusionner les df order by order id

    liste_order = [order_payments_2, order_reviews_2]
    for df in liste_order:
        orders_2 = pd.merge(orders_2, df,
                              how='inner',
                              left_on='order_id',
                              right_on='order_id'
                              )
    data = pd.merge(orders_2,customers_2,
                    how='left',
                    left_on='customer_id',
                    right_on='customer_id'
                          )



    data ['delay_in_delivery'] = data ['order_delivered_customer_date'] - data['order_estimated_delivery_date']
    data = data.dropna(how='any', subset=['delay_in_delivery'])
    data ['delay_in_delivery'] = data ['delay_in_delivery'].dt.days.round(0).astype(int)

    data = data.drop(columns=['customer_id','customer_zip_code_prefix','customer_city',
      'order_delivered_customer_date','order_estimated_delivery_date',
      'customer_state', 'order_status',
      'order_purchase_timestamp',
      'order_delivered_carrier_date'])

    return data

"""### B. Rfm level function"""

def rfm_level(df):
    if df['RFM_Score'] >= 10:
        return "Can't Loose Them"
    elif ((df['RFM_Score'] >= 9) and (df['RFM_Score'] < 10)):
        return 'Champions'
    elif ((df['RFM_Score'] >= 8) and (df['RFM_Score'] < 9)):
        return 'Loyal'
    elif ((df['RFM_Score'] >= 7) and (df['RFM_Score'] < 8)):
        return 'Potential'
    elif ((df['RFM_Score'] >= 6) and (df['RFM_Score'] < 7)):
        return 'Promising'
    elif ((df['RFM_Score'] >= 5) and (df['RFM_Score'] < 6)):
        return 'Needs Attention'
    else:
        return 'Require Activation'

"""### C. Elbow method: Optimal K"""

# K means

def Elbow(rfm):

  rfm_model = pd.DataFrame()
  rfm_model = rfm[['Recency','Monetary', 'delay_in_delivery','Review_score']] # 'delay_in_delivery',
  Standard = StandardScaler()
  x_scaled = pd.DataFrame()
  x_scaled = Standard.fit_transform(rfm_model)
  # x_scaled = Standard.fit(rfm_model)


  # Elbow method

  model = KMeans()
  visualizer = KElbowVisualizer(model, k=(2,8))
  visualizer.fit(x_scaled)
  optimal_k = visualizer.elbow_value_
  visualizer.show()

  return rfm_model, x_scaled, optimal_k

"""### D. Applying K-Means

"""

def kmeans(rfm_model, x_scaled, k):
  kmeans_scaled = KMeans(k)
  kmeans_scaled.fit(rfm_model)
  identified_clusters = kmeans_scaled.fit_predict(rfm_model)
  clusters_scaled = rfm_model.copy()
  clusters_scaled['cluster_pred']=kmeans_scaled.fit_predict(x_scaled)

  return clusters_scaled, kmeans_scaled

"""  sns.set(style="darkgrid")
  print(" Our cluster centers are as follows")
  print(kmeans_scaled.cluster_centers_)
  f, ax = plt.subplots(figsize=(15,7))
  ax = sns.countplot(x="cluster_pred", data=clusters_scaled)
  clusters_scaled.groupby(['cluster_pred']).count()"""

"""### E.Visualizing the clusters"""

def Plot3D(clusters_scaled):
  fig = plt.figure()
  ax = plt.axes(projection='3d')
  ax.view_init(30, 210)
  xline=clusters_scaled['Recency']
  yline=clusters_scaled['Review_score']
  zline=clusters_scaled['Monetary']

  ax.scatter3D(xline, zline,yline,c=clusters_scaled['cluster_pred'])

def visualizer(x_scaled, m):
  # 'calinski_harabasz' , 'silhouette_score'
  model = KMeans(random_state=123)
  visualizer = KElbowVisualizer(model, k=(2,8), metric= m, timings=True)
  visualizer.fit(x_scaled)
  visualizer.poof()

def Validation(x_scaled, kmeans_scaled,k):

  sil_score = silhouette_score(x_scaled, kmeans_scaled.labels_, metric='euclidean')
  print('Silhouette Score: %.2f' % sil_score)

  model = KMeans(k)
  visualizer = SilhouetteVisualizer(model)
  visualizer.fit(x_scaled)
  visualizer.poof()

def Snakeplot(rfm_melted, hue, title):
  sns.lineplot(x = 'metrics', y = 'value', hue = hue, data = rfm_melted)
  plt.title(title)
  plt.legend(loc = 'upper right')

def Cluster_description(rfm_model):

  colonne_cluster = ['Recency', 'Review_score', 'Monetary']
  for column in colonne_cluster:
      try:
          plt.figure(figsize=(10,6))
          titre = 'Moyenne de ' + str(column) + ' pour chaque cluster'
          plt.title(titre)
          sns.barplot(x = 'cluster',
                      y = column,
                      data = rfm_model,
                      ci="sd")
          plt.show()

      except:
          print('Erreur colonne : ', column)

"""### F. ARI and K-Means"""

# Define a function to create multiple data frames based on a base period and time lapse
def create_data_frames(base, timelapse):
    base_df = data2[(data2['order_approved_at'] >= data2['order_approved_at'].min()) & (data2['order_approved_at'] < data2['order_approved_at'].min() + pd.DateOffset(months=base))]
    data_frames = [base_df]
    max_date = data2['order_approved_at'].max()
    current_date = data2['order_approved_at'].min() + pd.DateOffset(months=timelapse)
    while current_date + pd.DateOffset(months=base) <= max_date:
        data_frames.append(data2[(data2['order_approved_at'] >= current_date) & (data2['order_approved_at'] < current_date + pd.DateOffset(months=timelapse+base))])
        current_date += pd.DateOffset(months=timelapse)
    return data_frames

def kmeans_pipe(dataframe):
  k_cluster = 0
  rfm = dataframe.groupby('customer_unique_id').agg({'order_approved_at' : lambda x : (now - x.max()).days,
                                'order_id': lambda num : len(num),
                                'payment_value': lambda price : price.sum()


                              })

  col_list = ['Recency','Frequency','Monetary']

  # Rename the columns

  rfm.rename(columns={'order_approved_at': 'Recency',
                          'order_id': 'Frequency',
                          'payment_value': 'Monetary'}, inplace=True)

  # Calculate Reviewscore

  Reviewscore = data2.drop_duplicates().groupby(
    by=['customer_unique_id'], as_index=False)['review_score'].mean()
  Reviewscore.columns = ['customer_unique_id', 'Review_score']

  # Calculate Delay_in_delivery

  Delay = data2.drop_duplicates().groupby(
      by=['customer_unique_id'], as_index=False)['delay_in_delivery'].mean()
  Delay.columns = ['customer_unique_id', 'delay_in_delivery']

  # Merge

  rfm = rfm.merge(Reviewscore, how='inner', on='customer_unique_id')
  rfm = rfm.merge(Delay, how='inner', on='customer_unique_id')

  rfm_model, x_scaled, k_cluster = Elbow(X)
  clusters_scaled, kmeans_scaled = kmeans(rfm_model, x_scaled, k_cluster)
  # clusters_scaled.groupby(['cluster_pred']).count()

  return rfm, rfm_model, x_scaled, clusters_scaled, kmeans_scaled

"""# I. Notebook de l'analyse exploratoire

---

### 1. Data Cleaning & exploration
"""

customers = pd.read_csv("/content/olist_customers_dataset.csv", sep=',',low_memory=False)
sellers = pd.read_csv("/content/olist_sellers_dataset.csv", sep=',',low_memory=False)
products = pd.read_csv("/content/olist_products_dataset.csv", sep=',',low_memory=False)
orders = pd.read_csv("/content/olist_orders_dataset.csv", sep=',',low_memory=False)
order_items = pd.read_csv("/content/olist_order_items_dataset.csv", sep=',',low_memory=False)
order_payments = pd.read_csv("/content/olist_order_payments_dataset.csv", sep=',',low_memory=False)
order_reviews = pd.read_csv("/content/olist_order_reviews_dataset.csv", sep=',',low_memory=False)
geolocation = pd.read_csv("/content/olist_geolocation_dataset.csv", sep=',',low_memory=False)
translation = pd.read_csv("/content/product_category_name_translation.csv", sep=',',low_memory=False)

liste_df = [customers,
            geolocation,
            order_items,
            order_payments,
            order_reviews,
            orders,products,
            sellers,
            translation]

data = nettoyage(liste_df)

data

data2 = data.copy().dropna().drop_duplicates()
data2.info()
now =  dt.datetime(2018,9,3)
data2['order_approved_at']= pd.to_datetime(data2['order_approved_at'])

rfm = data2.groupby('customer_unique_id').agg({'order_approved_at' : lambda x : (now - x.max()).days,
                              'order_id': lambda num : len(num),
                              'payment_value': lambda price : price.sum()


                             })

col_list = ['Recency','Frequency','Monetary']

# Rename the columns

rfm.rename(columns={'order_approved_at': 'Recency',
                         'order_id': 'Frequency',
                         'payment_value': 'Monetary'}, inplace=True)

plt.figure(figsize=(20,13))

plt.subplot(3,1,1);
sns.distplot(rfm['Recency'])
plt.ylabel('Proba', fontsize=12)
plt.xlabel('Recency', fontsize=12)

plt.subplot(3,1,2);
sns.distplot(rfm['Frequency'])
plt.ylabel('Proba', fontsize=12)
plt.xlabel('Frequency', fontsize=12)

plt.subplot(3,1,3);
sns.distplot(rfm['Monetary'])
plt.ylabel('Proba', fontsize=12)
plt.xlabel('Monetary', fontsize=12)

"""### 2. Features engineering & RFM segmentation"""

# Calculate Reviewscore

Reviewscore = data2.drop_duplicates().groupby(
    by=['customer_unique_id'], as_index=False)['review_score'].mean()
Reviewscore.columns = ['customer_unique_id', 'Review_score']

# Calculate Delay_in_delivery

Delay = data2.drop_duplicates().groupby(
    by=['customer_unique_id'], as_index=False)['delay_in_delivery'].mean()
Delay.columns = ['customer_unique_id', 'delay_in_delivery']

# Merge

rfm = rfm.merge(Reviewscore, how='inner', on='customer_unique_id')
rfm = rfm.merge(Delay, how='inner', on='customer_unique_id')

# --Calculate R, S, D, M groups--
# Create labels

r_labels = range(3, 0, -1)
s_labels = range(1, 4)
d_labels = range(1, 4)
m_labels = range(1, 4)

# Assign these labels to 3 equal percentile groups
r_groups = pd.qcut(rfm['Recency'], q=3, labels=r_labels,duplicates='drop')

# Assign these labels to 5 equal percentile groups
s_groups = pd.qcut(rfm['Review_score'],q=5, labels=s_labels, duplicates='drop')

# Assign these labels to 3 equal percentile groups
d_groups = pd.qcut(rfm['delay_in_delivery'], q=3, labels= d_labels, duplicates='drop')

# Assign these labels to 3 equal percentile groups
m_groups = pd.qcut(rfm['Monetary'], q=3, labels=s_labels)

# Create new columns R, S, M, D
rfm = rfm.assign(R = r_groups.values, S = s_groups.values, M = m_groups.values, D = d_groups.values )

# Calculation for RFM score (R+F+M)
def join_rfm(x): return str(x['R']) + str(x['S']) + str(x['M'])+ str(x['D'])
rfm['RFM_Segment_Concat'] = rfm.apply(join_rfm, axis=1)

# Calculate RFM_Score (method 2)
rfm['RFM_Score'] = rfm[['R','D','M','S']].sum(axis=1)

# Create a new variable RFM_Level
rfm['RFM_Level'] = rfm.apply(rfm_level, axis=1)
display(rfm.head())

rfm_stats = rfm.groupby('RFM_Level').agg({
    'Recency': 'mean',
    'Review_score':'mean',
    'delay_in_delivery':'mean',
    'Monetary':['mean','count']
}).round(1)

rfm_stats.columns = rfm_stats.columns.droplevel()
rfm_stats.columns = ['Recency_mean', 'Review_score', 'delay_in_delivery', 'Monetary_mean', 'Monetary_count' ]
display(rfm_stats)

# plotting a map based on segment stats
fig = plt.gcf()
ax=fig.add_subplot()
fig.set_size_inches(16,9)
squarify.plot(sizes = rfm_stats['Monetary_count'],
              label=["Can't Loose Them",'Champions','Loyal','Potential','Promising','Needs Attention','Require Activation'],
              color=['Green',"Orange",'Purple','Maroon', 'Pink', 'Teal', 'Red'],
              alpha = .6
              )
plt.title('rfm Segments', fontsize = 22, fontweight='bold')
plt.axis('off')
plt.show()

rfm

rfm.groupby('RFM_Level').agg({
    'Recency' : ['mean', 'min','max'],
    'Review_score' : ['mean', 'min','max'],
    'Frequency' : ['mean', 'min','max'],
    'delay_in_delivery': ['mean', 'min','max'],
    'Monetary' : ['mean','min','max','count']
})

# RFM Clustering
rfm.describe()

"""# Outlier treatment for recency, frequency, monetary

plt.boxplot(rfm.Recency)
Q1 = rfm.Recency.quantile(0.25)
Q3 = rfm.Recency.quantile(0.75)
IQR = Q3 - Q1
rfm = rfm[(rfm.Recency >= Q1 - 1.5*IQR) & (rfm.Recency <= Q3 + 1.5*IQR)]


plt.boxplot(rfm.Monetary)
Q1 = rfm.Monetary.quantile(0.25)
Q3 = rfm.Monetary.quantile(0.75)
IQR = Q3 - Q1
rfm = rfm[(rfm.Monetary >= (Q1 - 1.5*IQR)) & (rfm.Monetary <= (Q3 + 1.5*IQR))]

plt.boxplot(rfm.Review_score)
Q1 = rfm.Review_score.quantile(0.25)
Q3 = rfm.Review_score.quantile(0.75)
IQR = Q3 - Q1
rfm = rfm[(rfm.Review_score >= (Q1 - 1.5*IQR)) & (rfm.Review_score <= (Q3 + 1.5*IQR))]

plt.boxplot(rfm.delay_in_delivery)
Q1 = rfm.Review_score.quantile(0.25)
Q3 = rfm.Review_score.quantile(0.75)
IQR = Q3 - Q1
rfm = rfm[(rfm.delay_in_delivery >= (Q1 - 1.5*IQR)) & (rfm.delay_in_delivery <= (Q3 + 1.5*IQR))]"""

X = rfm.sample(9500, random_state=1).copy()

X

"""# II. Notebook d'essais
---

## 1. K-means
"""

# Elbow method
rfm_model, x_scaled, k_clusters = Elbow(X)

"""According to the Elbow method, the number of clusters is 4."""

clusters_scaled, kmeans_scaled = kmeans(rfm_model, x_scaled, k_clusters )

Plot3D(clusters_scaled)

visualizer(x_scaled,'calinski_harabasz')

Validation(x_scaled, kmeans_scaled,4)

"""## 2. DBSCAN"""

# https://www.kaggle.com/code/pnarerdoan/k-means-dbscan-clustering/notebook

epsilon = [1,1.25,1.5,1.75, 2,2.25,2.5,2.75, 3,3.25,3.5,3.75, 4]
min_samples = [10,15,20,25]

calinski_harabasz_avg = 0
calinski_avg = []
max_value = [0,0,0,0]

for i in range(len(epsilon)):
    for j in range(len(min_samples)):
      try:
        db = DBSCAN(min_samples = min_samples[j], eps =epsilon[i]).fit(x_scaled)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        labels = db.labels_

        # Number of clusters in labels, ignoring noise if present.
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_ = list(labels).count(-1)

        calinski_harabasz_avg = metrics.calinski_harabasz_score(x_scaled, labels)

        if calinski_harabasz_avg > max_value[3]:
            max_value=(epsilon[i], min_samples[j], n_clusters_, calinski_harabasz_avg)
        calinski_avg.append(calinski_harabasz_avg)
      except:
        s = 0

print("epsilon=", max_value[0],
      "\nmin_sample=", max_value[1],
      "\nnumber of clusters=", max_value[2],
      "\naverage calinski_harabasz score= %.4f" % max_value[3])

"""## 3. CAH"""

# Hierachical clustering model

calinski_harabasz_avg = 0
sil_avg = []
max_value = [0,0]
n_clusters = 2

for i in range(2,8):
  hc = AgglomerativeClustering(n_clusters = i).fit(x_scaled)
  core_samples_mask = np.zeros_like(hc.labels_, dtype=bool)


  labels = hc.labels_

  # Number of clusters in labels, ignoring noise if present.
  n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
  n_noise_ = list(labels).count(-1)

  calinski_harabasz_avg = metrics.calinski_harabasz_score(x_scaled, labels)

  if calinski_harabasz_avg > max_value[1]:
      max_value=(n_clusters_, calinski_harabasz_avg)
  sil_avg.append(calinski_harabasz_avg)

print("\nnumber of clusters=", max_value[0],
      "\naverage calinski_harabasz score= %.4f" % max_value[1])

"""## 4. GMM"""

n_components = [2, 3, 4, 5, 6]
n_init = [2,3,4,5,6]

calinski_harabasz_avg = 0
calinski_avg = []
max_value = [0, 0, 0, 0]
n_clusters = 1

for i in range(len(n_components)):
  for j in range(len(n_init)):
    try:
      gmm = GaussianMixture(n_components=n_components[i], n_init=n_init[j], random_state=1, tol=1e-4, init_params='kmeans', max_iter=1000,).fit(x_scaled)
      labels = gmm.predict(x_scaled)

      # Number of clusters in labels, ignoring noise if present.
      n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
      n_noise_ = list(labels).count(-1)

      calinski_harabasz_avg = metrics.calinski_harabasz_score(x_scaled, labels)

      if calinski_harabasz_avg > max_value[3]:
          max_value = [n_components[i], n_init[j], n_clusters_, calinski_harabasz_avg]
      calinski_avg.append(calinski_harabasz_avg)
    except:
      s = 0

print("n_components=", max_value[0],
      "\nn_init=", max_value[1],
      "\nnumber of clusters=", max_value[2],
      "\naverage calinski_harabasz score= %.4f" % max_value[3]
      )

"""# III. Notebook de simulation
---

## K-means on all Data
"""

rfm_model, x_scaled, k_clusters  = Elbow(rfm)

"""According to the Elbow method, the number of clusters is 4."""

kmeans_scaled = KMeans(4)
kmeans_scaled.fit(rfm_model)
identified_clusters = kmeans_scaled.fit_predict(rfm_model)
clusters_scaled = rfm_model.copy()
clusters_scaled['cluster_pred']=kmeans_scaled.fit_predict(x_scaled)
sns.set(style="darkgrid")
print(" Our cluster centers are as follows")
print(kmeans_scaled.cluster_centers_)
f, ax = plt.subplots(figsize=(15,7))
ax = sns.countplot(x="cluster_pred", data=clusters_scaled)
clusters_scaled.groupby(['cluster_pred']).count()

Plot3D(clusters_scaled)

visualizer(x_scaled,'calinski_harabasz')

"""## 1. Cluster Profiling"""

rfm_model['cluster']= clusters_scaled['cluster_pred']
rfm_model['level']=rfm['RFM_Level']

rfm_model.groupby('cluster').agg({
    'Recency' : ['mean','min','max'],
    'Review_score' : ['mean','min','max'],
    'Monetary' : ['mean','min','max','count']
})

rfm_scaled=pd.DataFrame()
rfm_scaled=rfm_model.copy()
scaler=StandardScaler()
rfm_scaled[['Recency', 'Review_score','Monetary']] = scaler.fit_transform(rfm_scaled[['Recency', 'Review_score','Monetary']])
rfm_scaled['cust_id']= rfm_model.index
display (rfm_scaled.head())


# Melting the dataframe

rfm_melted=pd.DataFrame()
rfm_melted = pd.melt(frame= rfm_scaled, id_vars= ['cust_id', 'level', 'cluster'], var_name = 'metrics', value_name = 'value')
display(rfm_melted.head())

"""## 2. Snake plot"""

# Snake plot based on RFM segmentation
Snakeplot(rfm_melted, 'level', 'Snake Plot of RFM')

# Snake plot with clusters using K-Means
Snakeplot(rfm_melted, 'cluster', 'Snake Plot of Clusters')

plt.figure(figsize=(15,6))
plt.title('Distribution du nombre d\'individus par cluster, en pourcentage')
sns.barplot(x = rfm_melted['cluster'].value_counts().index,
           y= rfm_melted['cluster'].value_counts().values/len(rfm_melted)*100)

"""## 3. Cluster Description"""

Cluster_description(rfm_model)

Cluster_description(rfm_scaled)

"""# IV. ARI"""

df = rfm[['Recency', 'Monetary','Review_score','delay_in_delivery']].copy()
data2 = data2.sort_values('order_approved_at', ascending=False)

# Enregistrement du DataFrame en tant que fichier CSV
csv_file_path = '/content/drive/My Drive/Colab Notebooks/df_project_4.csv'
df.to_csv(csv_file_path, index=False)

# Enregistrement du DataFrame en tant que fichier CSV
csv_file_path = '/content/drive/My Drive/Colab Notebooks/data2_project_4.csv'
data2.to_csv(csv_file_path, index=False)

# Create a data frame with a base and a timelapse

base = 12  # Base period (in months)
month_window = 1  # Month window
data_frames = create_data_frames(base, month_window)  # Generate data frames


# Print the number of data frames created
print(f"{len(data_frames)} data frames created.")

n = len(data_frames)
for i in range(0,n):
  print(len(data_frames[i]))

from sklearn.metrics import adjusted_rand_score
ari_values = []
base_df = data_frames[0]  # Use the same base data frame for each iteration
clustering1 = kmeans_pipe(base_df)[-1]  # Get the KMeans object from the last step of kmeans_pipe

for i in range(n):
    subsequent_df = data_frames[i]
    clustering2 = kmeans_pipe(subsequent_df)[-1]
    ari = adjusted_rand_score(clustering1.labels_, clustering2.labels_)
    ari_values.append(ari)

print(ari_values)

# Plot ARI Trends
plt.plot(time_points, ari_values, marker='o')
plt.xlabel('Time Points')
plt.ylabel('ARI Values')
plt.title('ARI Trends over Time')
plt.xticks(time_points)
plt.grid(True)
plt.show()

ari_values

"""The list of ARI values you provided represents the similarity between the clustering results of the base data frame and each subsequent data frame.

> Overall, the ARI values indicate a strong level of stability and consistency in the clustering results over time. The high ARI values indicate that the clustering patterns remain similar, with only minor variations observed in some cases. This suggests that the clustering approach captures meaningful patterns in the data and that the customer behavior or characteristics remain relatively consistent over the analyzed time periods.

***Sources:***
* https://github.com/smazzanti/are_you_still_using_elbow_method/blob/main/are-you-still-using-elbow-method.ipynb
* https://towardsdatascience.com/are-you-still-using-the-elbow-method-5d271b3063bd
* https://towardsdatascience.com/gaussian-mixture-models-vs-k-means-which-one-to-choose-62f2736025f0#:~:text=The%20first%20visible%20difference%20between,GMs%20is%20a%20probabilistic%20algorithm.
* https://www.google.com/search?q=watergate&rlz=1C1ONGR_frFR1031FR1031&oq=watergate&aqs=chrome..69i57j0i433i512l2j0i512l6j46i175i199i512.1596j0j7&sourceid=chrome&ie=UTF-8

***Table of Contents***
1. Introduction
   - Project Overview
   - Objective

2. Libraries and Helpers
   - List of Required Libraries
   - Helper Functions
     - Global Cleaning Function
     - RFM Level Function
     - Elbow Method for Optimal K
     - Applying K-Means
     - Visualizing the Clusters
     - ARI and K-Means

3. Notebook: Exploratory Analysis
   - Data Cleaning and Exploration
   - Features Engineering and RFM Segmentation

4. Notebook: Experimentation
   - K-means
   - DBSCAN
   - CAH
   - GMM

5. Notebook: Simulation
   - K-means on All Data
   - Cluster Profiling
   - Snake Plot
   - Cluster Description

6. ARI Evaluation

7. Conclusion
"""