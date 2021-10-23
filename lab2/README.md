# User points system

**The commands:**

Then start the application:
```
$ docker-compose up 
```
The above command will both create the images and start the containers (2 images and 2 containers - one for the FastAPI application and one for the MongoDB database).

For visualizing the application, open up your browser and enter:

* http://127.0.0.1/docs

## Testing 
1. under ``` checkoff/post_requests.http ``` run all the postrequests in that order one by one to seed the database

2. To ensure that things are seeded into the database, you can try to run the post_requests again like in step 1 or run the ```GET http://127.0.0.1/users HTTP/1.1``` in the ``` checkoff/get_requests.http ``` file which will retrieve all the users

3. As the data is not cached (bad practice here tried using lru_cache doesnt work), you can change the ```GET http://127.0.0.1/user/615dd6b4a18f3445b46f5520 HTTP/1.1 ``` The object_id behind the user with one of the ids listed in the get_all requests. It should work with a non 404 response.

4. Note that upon creation, all the users scores are set to 0 as default so before you run the get requests with params query, run the ```checkoff/put_requests.http``` file.

5. run the ```checkoff/delete_requests.http``` folder to see how to delete or not delete successfully
<br/>
<br/>

## Idempotent
In general, all the routes except those with the POST requests methods are idempotent as idempotent means that the requests can run many times withe the same result. For the GET requests, no matter how many times we run them, especially those that query by id, nothing in the database is changed. For that of the delete requests, You run the request for the first time, the user is successfully removed but subsequently it throws a 404 error of user that cannot be found. For that of the put requests, can also see the same effect as delete except for the fact that you are updating the user fields, running the exact same requests, will still mean that the user data is the same for that particular field in the database.

## Improvements in performance
1. To allow fast retrieval of the data, I should have cached the data on the post request. This will allow fast retrieval of the saved data from the database. Hence, I need not query the database at each request sent.
2. In terms of computational complexity, my current time complexity for the codes runs on a logarithmic run time with the python inbuilt functions. To improve, I should have pulled the data into a hashtable which would make indexing faster for the queries with the userid related.

3. For the deleting in batches, I should have limited the amount of data to send back to the server for huge datasets as to prevent the overhead of holding back some requests

