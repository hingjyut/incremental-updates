# incremental-updates
Cette démo utilise rabbitmq pour implémenter un système naïf de
mises à jour incrémentales. Ce système s'appuie sur la propriété
qui assure que les messages envoyés par le serveur sont reçus
par les clients dans le même ordre. Les clients s'abonnent
auprès du serveur pour recevoir des mises à jour d'un programme donné
(représenté par une chaîne de caractère) lorsqu'ils s'y
connectent pour la première fois. Dès lors, chaque fois
que le serveur émet une mise à jour (représenté par une substition
de chaîne dans la chaîne de caractère du programme), le client
la reçoit et l'applique à sa propre version. L'ordre de
réception des mises à jour est important car les opérations
de substitution dans une chaîne de caractère ne commutent pas.
Le stockage des queues de mise à jour de chaque client dans
Rabbitmq permet de s'assurer qu'un client recevra l'intégralité
des mises à jour qu'il a raté pendant sa déconnexion.

## Usage
D'abord lancer rabbitmq comme-ci
```
> sudo docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
Puis lancer le serveur comme suit
```
> python3 server.py
What is your software name? test
Please type the first version below:
abc
 [x] Awaiting RPC requests
Do you want to publish an update?y
 update begin: 1
 update end: 2
 update content: rna
 old version: abc
 new version: arnac
Publishing update 1 to the people
Do you want to publish an update?Got a new client request # Cette ligne coïncide avec le lancement de la commande ci-dessous
Just added new client 9938d4e0-0af7-47df-aef3-acfe67c5b9ba
y
 update begin: 2
 update end: 3
 update content: coucou
 old version: arnac
 new version: arcoucouac
Publishing update 2 to the people
Do you want to publish an update?y
 update begin: 0  
 update end: -5
 update content: test
 old version: arcoucouac
 new version: testcouac
Publishing update 3 to the people
Do you want to publish an update?y
 update begin: 0
 update end: 0
 update content: test1
 old version: testcouac
 new version: test1testcouac
Publishing update 4 to the people
Do you want to publish an update?y
 update begin: 0
 update end: 0
 update content: test2
 old version: test1testcouac
 new version: test2test1testcouac
Publishing update 5 to the people
Do you want to publish an update?n
Publishing update 2 to the people
```
et pour le client
```
> python3 client.py 
What is your software name? test
About to ask for a new UUID
Got a response
Got a new UUID
Got a new update!
 old version: arnac
 new version: arcoucouac
 hash before update: d68d19cbcb...
 hash after update: 415f4a61b6...
 hash expect: 415f4a61b6...
Incremental update successful!
^CTraceback (most recent call last):
# ...
KeyboardInterrupt

> python3 client.py 
What is your software name? test
Got a new update!
 old version: arcoucouac
 new version: testcouac
 hash before update: 415f4a61b6...
 hash after update: 69ff681723...
 hash expect: 69ff681723...
Incremental update successful!
^CTraceback (most recent call last):
# ...
KeyboardInterrupt

> python3 client.py 
What is your software name? test
Got a new update!
 old version: testcouac
 new version: test1testcouac
 hash before update: 69ff681723...
 hash after update: 03ea267417...
 hash expect: 03ea267417...
Incremental update successful!
Got a new update!
 old version: test1testcouac
 new version: test2test1testcouac
 hash before update: 03ea267417...
 hash after update: 7b73f5ddc3...
 hash expect: 7b73f5ddc3...
Incremental update successful!
^CTraceback (most recent call last):
# ...
KeyboardInterrupt
```